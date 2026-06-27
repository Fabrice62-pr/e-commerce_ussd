from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "product_count")
    list_filter = ("is_active",)
    search_fields = ("name",)

    @admin.display(description="Nombre de produits")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "is_available")
    list_filter = ("is_active", "category")
    search_fields = ("name", "description")
    list_editable = ("price", "stock", "is_active")   # édition rapide depuis la liste
    list_select_related = ("category",)

    @admin.display(boolean=True, description="Disponible")
    def is_available(self, obj):
        return obj.is_available
