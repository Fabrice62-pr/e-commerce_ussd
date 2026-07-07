"""Routage principal des URLs du projet."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Interface d'administration web (gestion produits, commandes, rapports)
    path("admin/", admin.site.urls),
    # Tableau de bord des rapports (réservé au personnel) -> /rapports/
    path("", include("orders.urls")),
    # Webhook USSD (appelé par la passerelle) -> /ussd/callback/
    path("ussd/", include("ussd.urls")),
]
