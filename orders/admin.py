from django.contrib import admin, messages

from .models import (
    CustomerUSSD,
    DejaPayeeError,
    Order,
    OrderItem,
    PaiementError,
)


@admin.register(CustomerUSSD)
class CustomerUSSDAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "name", "language", "order_count", "created_at")
    list_filter = ("language",)
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
    actions = ["action_valider_paiement"]

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
