from django.contrib import admin

from .models import CustomerUSSD, Order, OrderItem


@admin.register(CustomerUSSD)
class CustomerUSSDAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "name", "order_count", "created_at")
    search_fields = ("phone_number", "name")

    @admin.display(description="Nombre de commandes")
    def order_count(self, obj):
        return obj.orders.count()


class OrderItemInline(admin.TabularInline):
    """Affiche les lignes directement dans la page d'une commande."""

    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)
    autocomplete_fields = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "status",
        "total_amount",
        "validation_code",
        "is_paid",
        "created_at",
    )
    list_filter = ("status", "is_paid", "created_at")
    search_fields = ("validation_code", "customer__phone_number", "customer__name")
    readonly_fields = ("validation_code", "total_amount", "created_at", "updated_at")
    inlines = [OrderItemInline]
    list_select_related = ("customer",)

    def save_related(self, request, form, formsets, change):
        """Recalcule le montant total de la commande après l'enregistrement des lignes."""
        super().save_related(request, form, formsets, change)
        form.instance.update_total()
