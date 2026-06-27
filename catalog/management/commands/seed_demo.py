"""Peuple la base avec des catégories et produits de démonstration.

Usage :  docker compose exec web python manage.py seed_demo

Idempotent : relancer la commande ne crée pas de doublons (get_or_create).
"""
from django.core.management.base import BaseCommand

from catalog.models import Category, Product

# Catégorie -> liste de (nom, prix XOF, stock, description)
DEMO_DATA = {
    "Vivres": [
        ("Riz 25kg", 12000, 40, "Sac de riz parfumé de 25 kg."),
        ("Huile 1L", 3500, 60, "Bouteille d'huile végétale 1 litre."),
        ("Sucre 1kg", 1000, 100, "Paquet de sucre en poudre 1 kg."),
        ("Farine 5kg", 4500, 30, "Sac de farine de blé 5 kg."),
    ],
    "Hygiène": [
        ("Savon", 500, 200, "Savon de ménage."),
        ("Dentifrice", 1200, 80, "Tube de dentifrice."),
        ("Lessive 1kg", 1500, 50, "Paquet de lessive en poudre 1 kg."),
    ],
    "Boissons": [
        ("Eau 1.5L", 400, 150, "Bouteille d'eau minérale 1,5 litre."),
        ("Jus 1L", 1800, 45, "Brique de jus de fruits 1 litre."),
        ("Thé", 800, 70, "Boîte de thé en sachets."),
    ],
}


class Command(BaseCommand):
    help = "Crée des catégories et produits de démonstration."

    def handle(self, *args, **options):
        n_cat, n_prod = 0, 0
        for category_name, products in DEMO_DATA.items():
            category, created = Category.objects.get_or_create(name=category_name)
            n_cat += int(created)
            for name, price, stock, description in products:
                _, created = Product.objects.get_or_create(
                    name=name,
                    category=category,
                    defaults={
                        "price": price,
                        "stock": stock,
                        "description": description,
                    },
                )
                n_prod += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Données de démo prêtes : {n_cat} catégorie(s) et "
                f"{n_prod} produit(s) ajouté(s)."
            )
        )
