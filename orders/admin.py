from django.contrib import admin, messages
from django.utils.html import format_html

from .models import (
    CustomerUSSD,
    DejaPayeeError,
    Order,
    OrderItem,
    PaiementError,
)

# Statut -> variante de badge (mêmes couleurs sémantiques que la page Rapports).
STATUS_BADGE = {
    Order.Status.EN_ATTENTE: "warn",
    Order.Status.PAYEE: "ok",
    Order.Status.PREPAREE: "info",
    Order.Status.LIVREE: "teal",
    Order.Status.ANNULEE: "danger",
}


@admin.register(CustomerUSSD)
class CustomerUSSDAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "name",
        "language",
        "order_count",
        "cart_items",
        "cart_updated_at",
        "created_at",
    )
    list_filter = ("language",)
    search_fields = ("phone_number", "name")
    readonly_fields = ("cart", "cart_updated_at", "created_at")

    @admin.display(description="Nombre de commandes")
    def order_count(self, obj):
        return obj.orders.count()

    @admin.display(description="Panier en cours")
    def cart_items(self, obj):
        """Nombre d'articles dans le panier non validé du client."""
        return sum(item.get("qty", 0) for item in (obj.cart or []))


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
        "status_badge",
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
    actions = ["action_valider_paiement"]
    date_hierarchy = "created_at"  # navigation par période au-dessus de la liste
    fieldsets = (
        (None, {"fields": ("customer", "status", "is_paid")}),
        ("Paiement", {"fields": ("validation_code", "total_amount")}),
        ("Dates", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, obj):
        """Badge coloré : même code couleur que le tableau de bord des rapports."""
        variant = STATUS_BADGE.get(obj.status, "neutral")
        return format_html(
            '<span class="mts-badge mts-badge--{}">{}</span>',
            variant,
            obj.get_status_display(),
        )

    def save_related(self, request, form, formsets, change):
        """Recalcule le montant total de la commande après l'enregistrement des lignes."""
        super().save_related(request, form, formsets, change)
        form.instance.update_total()

    @admin.action(description="Valider le paiement (→ PAYEE, décrémente le stock)")
    def action_valider_paiement(self, request, queryset):
        """Valide le paiement des commandes sélectionnées.

        Workflow agent : rechercher la commande par son code de paiement (champ de
        recherche ci-dessus), la cocher, puis lancer cette action.
        """
        succes = 0
        for order in queryset:
            try:
                order.valider_paiement()
                succes += 1
            except DejaPayeeError as err:
                self.message_user(request, str(err), level=messages.WARNING)
            except PaiementError as err:
                self.message_user(request, f"Commande #{order.pk} : {err}", level=messages.ERROR)

        if succes:
            self.message_user(
                request,
                f"{succes} commande(s) validée(s) : statut PAYEE et stock décrémenté.",
                level=messages.SUCCESS,
            )
