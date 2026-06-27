"""Routage principal des URLs du projet."""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Interface d'administration web (gestion produits, commandes, rapports)
    path("admin/", admin.site.urls),
    # Les routes USSD seront ajoutées en Phase 3 :
    # path("ussd/", include("ussd.urls")),
]
