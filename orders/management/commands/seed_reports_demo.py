"""Génère un historique de commandes de démonstration, réparti sur plusieurs mois.

But : donner au tableau de bord des rapports (/rapports/) des données réalistes
sur plusieurs mois, pour illustrer les graphiques d'évolution (CA, stock, gains/
pertes). Sans cela, les rapports n'auraient que les commandes créées "aujourd'hui"
et les courbes seraient plates.

Tout passe par le VRAI moteur métier (Order.valider_paiement()) : le stock est
donc réellement décrémenté, comme si ces ventes avaient vraiment eu lieu. Les
commandes et clients de démo sont marqués distinctement (préfixe de téléphone
"+000DEMO") pour rester identifiables et supprimables sans toucher aux données
réelles ou aux commandes de test créées manuellement.

Usage :
    docker compose exec web python manage.py seed_reports_demo
    docker compose exec web python manage.py seed_reports_demo --reset   # relance propre
    docker compose exec web python manage.py seed_reports_demo --months 7 --reset
"""
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import Product
from orders.models import CustomerUSSD, Order, OrderItem, StockInsuffisantError

DEMO_PHONE_PREFIX = "+000DEMO"

# Stock de départ "généreux" pour la simulation, afin que l'historique généré
# reste cohérent avec un stock actuel plausible en fin de période. Deux
# produits sont volontairement sous-approvisionnés pour illustrer l'alerte
# stock bas / rupture dans les rapports (comme un vrai commerce qui viendrait
# de bien vendre sur ces références).
STOCK_DE_DEPART = {
    "Thé": 18,
    "Sucre 1kg": 22,
}
STOCK_DE_DEPART_DEFAUT_MIN = 120  # tous les autres produits sont boostés à ce plancher


class Command(BaseCommand):
    help = "Génère un historique de commandes de démonstration sur plusieurs mois."

    def add_arguments(self, parser):
        parser.add_argument(
            "--months", type=int, default=7,
            help="Nombre de mois d'historique à générer (mois courant inclus). Défaut : 7.",
        )
        parser.add_argument(
            "--reset", action="store_true",
            help="Supprime d'abord les commandes/clients de démo existants et "
                 "réinitialise le stock des produits concernés avant de regénérer.",
        )

    def handle(self, *args, **options):
        months = options["months"]
        products = list(Product.objects.filter(is_active=True))
        if not products:
            self.stderr.write(self.style.ERROR(
                "Aucun produit actif. Lancez d'abord : python manage.py seed_demo"
            ))
            return

        if options["reset"]:
            self._reset(products)

        self._boost_stock(products)
        customers = self._make_demo_customers(n=18)

        today = timezone.localdate()
        month_starts = self._last_n_month_starts(today, months)

        created_orders = 0
        with transaction.atomic():
            for i, month_start in enumerate(month_starts):
                is_current_month = i == len(month_starts) - 1
                n_orders = random.randint(10, 18)
                for _ in range(n_orders):
                    order_date = self._random_datetime_in_month(
                        month_start, today, is_current_month
                    )
                    if self._create_one_order(customers, products, order_date, is_current_month):
                        created_orders += 1

        self.stdout.write(self.style.SUCCESS(
            f"Historique de démo généré : {created_orders} commande(s) sur "
            f"{months} mois (clients préfixés « {DEMO_PHONE_PREFIX} »)."
        ))
        self.stdout.write(
            "Astuce : relancez avec --reset pour régénérer proprement, ou "
            "consultez /rapports/ pour voir le résultat."
        )

    # -- Préparation ------------------------------------------------------

    def _reset(self, products):
        """Supprime les commandes/clients de démo précédents (pas les vraies données)."""
        demo_customers = CustomerUSSD.objects.filter(phone_number__startswith=DEMO_PHONE_PREFIX)
        nb_orders = Order.objects.filter(customer__in=demo_customers).count()
        # Les OrderItem partent en cascade avec leur commande (on_delete=CASCADE).
        Order.objects.filter(customer__in=demo_customers).delete()
        nb_customers = demo_customers.count()
        demo_customers.delete()  # sûr maintenant : plus aucune commande ne les référence (PROTECT)

        # Remet le stock des produits ciblés à leur valeur de départ curatée, pour un
        # reset reproductible (les autres produits gardent leur stock actuel + reboost).
        for name, stock in STOCK_DE_DEPART.items():
            Product.objects.filter(name=name).update(stock=stock)

        self.stdout.write(
            f"Reset : {nb_orders} commande(s) et {nb_customers} client(s) de démo supprimés."
        )

    def _boost_stock(self, products):
        """Porte le stock à un plancher confortable avant de simuler des ventes."""
        for p in products:
            cible = STOCK_DE_DEPART.get(p.name)
            if cible is not None:
                if p.stock < cible:
                    p.stock = cible
                    p.save(update_fields=["stock"])
            elif p.stock < STOCK_DE_DEPART_DEFAUT_MIN:
                p.stock = STOCK_DE_DEPART_DEFAUT_MIN
                p.save(update_fields=["stock"])

    def _make_demo_customers(self, n):
        customers = []
        for i in range(1, n + 1):
            customer, _ = CustomerUSSD.objects.get_or_create(
                phone_number=f"{DEMO_PHONE_PREFIX}{i:03d}",
                defaults={"name": f"Client démo {i}"},
            )
            customers.append(customer)
        return customers

    def _last_n_month_starts(self, today, n):
        """Le 1er de chaque mois, du plus ancien au plus récent (mois courant inclus)."""
        y, m = today.year, today.month
        starts = []
        for _ in range(n):
            starts.append(datetime(y, m, 1))
            m -= 1
            if m == 0:
                m, y = 12, y - 1
        return list(reversed(starts))

    def _random_datetime_in_month(self, month_start, today, is_current_month):
        """Instant aléatoire dans le mois (jamais dans le futur pour le mois courant)."""
        if is_current_month:
            last_day = today
        else:
            next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            last_day = (next_month - timedelta(days=1)).date()
        day = random.randint(1, max(last_day.day, 1))
        naive = datetime(month_start.year, month_start.month, day,
                          random.randint(8, 19), random.randint(0, 59))
        return timezone.make_aware(naive)

    # -- Génération d'une commande -----------------------------------------

    def _create_one_order(self, customers, products, order_date, is_current_month):
        """Crée une commande complète et backdatée. Retourne True si créée."""
        customer = random.choice(customers)
        # Deux produits sont favorisés pour illustrer l'alerte stock bas en fin de période.
        weighted_products = products + [
            p for p in products if p.name in STOCK_DE_DEPART for _ in range(3)
        ]
        chosen = random.sample(weighted_products, k=min(random.randint(1, 3), len(products)))
        chosen = list(dict.fromkeys(chosen))  # dédoublonne en gardant l'ordre

        order = Order.objects.create(customer=customer)
        for product in chosen:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=random.randint(1, 4),
                unit_price=product.price,
            )
        order.update_total()

        # Répartition des statuts : la plupart aboutissent en paiement, une partie
        # est annulée (= "pertes"), le reste reste en attente (plus fréquent sur le
        # mois courant, comme dans la réalité d'un système qui tourne encore).
        outcome_roll = random.random()
        attente_seuil = 0.35 if is_current_month else 0.08
        try:
            if outcome_roll < attente_seuil:
                pass  # reste EN_ATTENTE
            elif outcome_roll < attente_seuil + 0.15:
                order.status = Order.Status.ANNULEE
                order.save(update_fields=["status", "updated_at"])
            else:
                order.valider_paiement()
                # Certaines commandes payées avancent jusqu'à Livrée/Préparée pour
                # varier la répartition par statut affichée dans les rapports.
                suite_roll = random.random()
                if suite_roll < 0.35:
                    order.status = Order.Status.LIVREE
                    order.save(update_fields=["status", "updated_at"])
                elif suite_roll < 0.55:
                    order.status = Order.Status.PREPAREE
                    order.save(update_fields=["status", "updated_at"])
        except StockInsuffisantError:
            # Rupture simulée : la commande n'a pas pu être honorée -> perte.
            order.status = Order.Status.ANNULEE
            order.save(update_fields=["status", "updated_at"])

        # Backdatage : contourne auto_now_add/auto_now en passant par une requête
        # UPDATE (n'invoque pas Model.save(), donc les règles auto_now ne se
        # ré-appliquent pas).
        updated_at = order_date + timedelta(minutes=random.randint(5, 240))
        Order.objects.filter(pk=order.pk).update(
            created_at=order_date, updated_at=updated_at
        )
        return True
