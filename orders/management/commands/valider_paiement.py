"""Valide le paiement d'une commande à partir de son code (workflow agent).

Usage :
    docker compose exec web python manage.py valider_paiement A7K2M9
"""
from django.core.management.base import BaseCommand, CommandError

from orders.models import Order, PaiementError


class Command(BaseCommand):
    help = "Valide le paiement d'une commande via son code de paiement."

    def add_arguments(self, parser):
        parser.add_argument("code", help="Code de paiement (6 caractères).")

    def handle(self, *args, **options):
        code = options["code"].strip().upper()

        try:
            order = Order.objects.get(validation_code=code)
        except Order.DoesNotExist:
            raise CommandError(f"Aucune commande trouvée pour le code « {code} ».")

        try:
            order.valider_paiement()
        except PaiementError as err:
            raise CommandError(str(err))

        self.stdout.write(
            self.style.SUCCESS(
                f"Paiement validé pour la commande #{order.pk} "
                f"(montant {order.total_amount} F). "
                f"Statut : {order.get_status_display()}. Stock décrémenté."
            )
        )
