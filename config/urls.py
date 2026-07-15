"""Routage principal des URLs du projet."""
from django.contrib import admin
from django.urls import include, path

# Personnalisation de l'accueil de l'administration.
admin.site.site_url = None  # retire « Voir le site » : la boutique n'a pas de site public (USSD)
admin.site.index_title = "Gestion de la boutique"

urlpatterns = [
    # Interface d'administration web (gestion produits, commandes, rapports)
    path("admin/", admin.site.urls),
    # Tableau de bord des rapports (réservé au personnel) -> /rapports/
    path("", include("orders.urls")),
    # Webhook USSD (appelé par la passerelle) -> /ussd/callback/
    path("ussd/", include("ussd.urls")),
]
