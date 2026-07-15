"""Calcul des statistiques pour le tableau de bord administrateur (rapports).

Correspond au « RapportService » anticipé dans les diagrammes UML.
"""
from django.db.models import Count, F, Sum

from catalog.models import Product

from .models import Order, OrderItem


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
    }
