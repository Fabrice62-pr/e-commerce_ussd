from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html

from .models import Category, Product


class LowStockFilter(admin.SimpleListFilter):
    """Filtre « Stock bas » : stock ≤ seuil d'alerte du produit."""

    title = "Niveau de stock"
    parameter_name = "niveau_stock"

    def lookups(self, request, model_admin):
        return [
            ("rupture", "En rupture (0)"),
            ("bas", "Stock bas (alerte)"),
            ("ok", "Stock suffisant"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "rupture":
            return queryset.filter(stock=0)
        if self.value() == "bas":
            return queryset.filter(stock__lte=F("low_stock_threshold"))
        if self.value() == "ok":
            return queryset.filter(stock__gt=F("low_stock_threshold"))
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "product_count")
    list_filter = ("is_active",)
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "is_active")}),
        (
            "Traductions du nom (laisser vide = affichage en français)",
            {
                "classes": ("collapse",),
                "fields": ("name_ha", "name_dyu", "name_ff", "name_wo"),
            },
        ),
    )

    @admin.display(description="Nombre de produits")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock",
        "low_stock_threshold",
        "stock_alert",
        "is_active",
    )
    list_filter = (LowStockFilter, "is_active", "category")
    search_fields = ("name", "description")
    list_editable = ("price", "stock", "low_stock_threshold", "is_active")
    list_select_related = ("category",)
    fieldsets = (
        (None, {"fields": ("category", "name", "price", "description", "is_active")}),
        ("Stock", {"fields": ("stock", "low_stock_threshold")}),
        (
            "Traductions du nom (laisser vide = affichage en français)",
            {
                "classes": ("collapse",),
                "fields": ("name_ha", "name_dyu", "name_ff", "name_wo"),
            },
        ),
    )

    @admin.display(description="Alerte")
    def stock_alert(self, obj):
        """Pastille visuelle : rupture / stock bas / OK."""
        if obj.stock == 0:
            couleur, libelle = "#c0392b", "RUPTURE"
        elif obj.is_low_stock:
            couleur, libelle = "#d9822b", "STOCK BAS"
        else:
            couleur, libelle = "#2e7d5b", "OK"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;font-weight:600;">{}</span>',
            couleur,
            libelle,
        )
