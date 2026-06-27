"""Simulateur de téléphone USSD en ligne de commande.

Imite le comportement d'Africa's Talking : à chaque saisie, on accumule
l'historique (séparé par '*') et on l'envoie au moteur, exactement comme la
vraie passerelle. Permet de tester tout le parcours sans connexion externe.

Usage (terminal interactif) :
    docker compose exec web python manage.py ussd_sim
    docker compose exec web python manage.py ussd_sim --phone +22790000099
"""
import uuid

from django.core.management.base import BaseCommand

from ussd.engine import process_ussd


class Command(BaseCommand):
    help = "Simule une session USSD dans le terminal."

    def add_arguments(self, parser):
        parser.add_argument(
            "--phone",
            default="+22790000099",
            help="Numéro de téléphone simulé.",
        )
        parser.add_argument(
            "--session",
            default=None,
            help="Identifiant de session (par défaut : généré aléatoirement).",
        )

    def handle(self, *args, **options):
        phone = options["phone"]
        session_id = options["session"] or f"sim-{uuid.uuid4().hex[:12]}"

        self.stdout.write(self.style.WARNING("=== Simulateur USSD MTS Shop ==="))
        self.stdout.write(f"Telephone : {phone}")
        self.stdout.write(f"Session   : {session_id}")
        self.stdout.write("(Tapez votre choix puis Entree. Ctrl+C pour quitter.)\n")

        history = []
        # Premier appel : text vide (le client vient de composer le code USSD)
        response = process_ussd(session_id, phone, "")
        self._render(response)

        while response.startswith("CON"):
            try:
                user_input = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                self.stdout.write("\n[Session interrompue]")
                return

            history.append(user_input)
            text = "*".join(history)
            response = process_ussd(session_id, phone, text)
            self._render(response)

        self.stdout.write(self.style.SUCCESS("\n[Session terminee]"))

    def _render(self, response):
        """Affiche la réponse comme sur un écran de téléphone."""
        prefix, _, body = response.partition(" ")
        self.stdout.write("\n" + "-" * 32)
        self.stdout.write(body)
        self.stdout.write("-" * 32)
        if prefix == "END":
            return
