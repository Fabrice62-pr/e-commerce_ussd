"""Calcul des statistiques pour le tableau de bord administrateur (rapports).

Correspond au « RapportService » anticipé dans les diagrammes UML.

Définition des indicateurs financiers (pour lever toute ambiguïté) :
  - CA généré   = somme de total_amount de TOUTES les commandes créées sur la
                  période (indicateur de demande brute, payées ou non).
  - Gains       = somme de total_amount des commandes PAYÉES (is_paid=True) :
                  le revenu réellement encaissé.
  - Pertes      = somme de total_amount des commandes ANNULÉES : le revenu perdu
                  (annulation, rupture de stock, abandon).
  - Résultat net = Gains − Pertes.
Le reste du CA généré (ni gains, ni pertes) correspond aux commandes encore
EN_ATTENTE de paiement.
"""
from datetime import datetime

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from catalog.models import Product

from .models import Order, OrderItem

MONTHS_FR = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc",
]


def get_rapport_data():
    """Retourne les indicateurs clés du tableau de bord."""
    orders = Order.objects
    paid = orders.filter(is_paid=True)

    # --- Indicateurs principaux ---
    chiffre_affaires = paid.aggregate(total=Sum("total_amount"))["total"] or 0
    nb_commandes = orders.count()
    nb_payees = paid.count()
    panier_moyen = int(chiffre_affaires / nb_payees) if nb_payees else 0
    nb_clients = orders.values("customer").distinct().count()

    # --- Répartition des commandes par statut ---
    statut_labels = dict(Order.Status.choices)
    par_statut = []
    for row in orders.values("status").annotate(n=Count("id")).order_by("-n"):
        par_statut.append(
            {
                "code": row["status"],  # sert au template pour la couleur sémantique
                "statut": statut_labels.get(row["status"], row["status"]),
                "n": row["n"],
                "pct": round(row["n"] * 100 / nb_commandes) if nb_commandes else 0,
            }
        )

    # --- Produits les plus vendus (sur les commandes payées) ---
    top_produits = list(
        OrderItem.objects.filter(order__is_paid=True)
        .values("product__name")
        .annotate(quantite=Sum("quantity"), ca=Sum("line_total"))
        .order_by("-quantite")[:10]
    )

    # --- Alerte stock bas (stock ≤ seuil d'alerte du produit) ---
    produits_stock_bas = list(
        Product.objects.filter(is_active=True, stock__lte=F("low_stock_threshold"))
        .select_related("category")
        .order_by("stock")
    )

    monthly = get_monthly_evolution()
    stock_evolution = get_stock_evolution()

    dernier_mois = monthly[-1] if monthly else None
    total_gains = dernier_mois["gains_cumules"] if dernier_mois else 0
    total_pertes = dernier_mois["pertes_cumulees"] if dernier_mois else 0

    return {
        "chiffre_affaires": chiffre_affaires,
        "nb_commandes": nb_commandes,
        "nb_payees": nb_payees,
        "nb_en_attente": nb_commandes - nb_payees,
        "panier_moyen": panier_moyen,
        "nb_clients": nb_clients,
        "par_statut": par_statut,
        "top_produits": top_produits,
        "produits_stock_bas": produits_stock_bas,
        "nb_stock_bas": len(produits_stock_bas),
        "monthly": monthly,
        "stock_evolution": stock_evolution,
        "cumul": {
            "ca": dernier_mois["ca_cumule"] if dernier_mois else 0,
            "gains": total_gains,
            "pertes": total_pertes,
            "net": total_gains - total_pertes,
        },
    }


def _last_n_months(n=7):
    """Liste de (année, mois) des n derniers mois, du plus ancien au plus récent."""
    today = timezone.localdate()
    y, m = today.year, today.month
    months = []
    for _ in range(n):
        months.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return list(reversed(months))


def get_monthly_evolution(n_months=7):
    """Série mensuelle : CA généré, nombre de commandes, gains, pertes, cumuls.

    Tout est calculé par agrégation SQL sur les vraies commandes en base (y
    compris l'historique de démonstration généré par `seed_reports_demo`, le
    cas échéant) — aucune valeur n'est codée en dur côté template.
    """
    months = _last_n_months(n_months)

    rows = (
        Order.objects.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            nb=Count("id"),
            ca=Sum("total_amount"),
            gains=Sum("total_amount", filter=Q(is_paid=True)),
            pertes=Sum("total_amount", filter=Q(status=Order.Status.ANNULEE)),
        )
    )
    by_month = {
        (row["month"].year, row["month"].month): row for row in rows if row["month"]
    }

    today = timezone.localdate()
    result = []
    cum_ca = cum_gains = cum_pertes = 0
    for (y, m) in months:
        row = by_month.get((y, m), {})
        ca = row.get("ca") or 0
        gains = row.get("gains") or 0
        pertes = row.get("pertes") or 0
        cum_ca += ca
        cum_gains += gains
        cum_pertes += pertes
        result.append(
            {
                "label": MONTHS_FR[m - 1],
                "year": y,
                "month": m,
                "ca": ca,
                "commandes": row.get("nb") or 0,
                "gains": gains,
                "pertes": pertes,
                "net": gains - pertes,
                "ca_cumule": cum_ca,
                "gains_cumules": cum_gains,
                "pertes_cumulees": cum_pertes,
                "net_cumule": cum_gains - cum_pertes,
                "is_current": (y == today.year and m == today.month),
            }
        )
    return result


def get_stock_evolution(limit=8):
    """Stock initial (déduit) / actuel / vendu, pour les produits les plus actifs.

    Le stock initial n'est pas stocké tel quel (pas d'historique de stock en
    base) : il est déduit par construction — stock_initial = stock_actuel +
    quantité totale vendue (commandes payées) — ce qui reste toujours exact,
    quelle que soit la façon dont le stock a évolué.
    """
    products = Product.objects.filter(is_active=True).select_related("category")
    sold_map = dict(
        OrderItem.objects.filter(order__is_paid=True)
        .values("product_id")
        .annotate(total=Sum("quantity"))
        .values_list("product_id", "total")
    )

    result = []
    for p in products:
        vendu = sold_map.get(p.id, 0)
        result.append(
            {
                "name": p.name,
                "actuel": p.stock,
                "vendu": vendu,
                "initial": p.stock + vendu,
            }
        )
    result.sort(key=lambda x: -x["vendu"])
    return result[:limit]
