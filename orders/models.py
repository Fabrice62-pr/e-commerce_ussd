import secrets

from django.db import models, transaction
from django.db.models import F

from catalog.models import Product


class PaiementError(Exception):
    """Erreur lors de la validation d'un paiement."""


class DejaPayeeError(PaiementError):
    """La commande a déjà été payée (double validation interdite)."""


class StockInsuffisantError(PaiementError):
    """Le stock d'un produit est devenu insuffisant au moment du paiement."""


def generate_validation_code():
    """Génère un code de validation alphanumérique de 6 caractères, ex. « A7K2M9 ».

    - Toujours un mélange : au moins une lettre ET au moins un chiffre.
    - On évite les caractères ambigus (0/O, 1/I) pour faciliter la dictée au comptoir.
    - L'unicité est garantie par le champ `unique=True` + une nouvelle tentative
      en cas de collision (voir Order.save).
    """
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    digits = "23456789"
    alphabet = letters + digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        # On re-tire tant que le code n'a pas au moins une lettre et un chiffre.
        if any(c in letters for c in code) and any(c in digits for c in code):
            return code


class CustomerUSSD(models.Model):
    """Client identifié uniquement par son numéro de téléphone (pas de compte web)."""

    phone_number = models.CharField("Numéro de téléphone", max_length=20, unique=True)
    name = models.CharField("Nom", max_length=100, blank=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Client USSD"
        verbose_name_plural = "Clients USSD"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or self.phone_number


class Order(models.Model):
    """Commande passée par un client via le menu USSD."""

    class Status(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente de paiement"
        PAYEE = "PAYEE", "Payée"
        PREPAREE = "PREPAREE", "Préparée"
        LIVREE = "LIVREE", "Livrée"
        ANNULEE = "ANNULEE", "Annulée"

    customer = models.ForeignKey(
        CustomerUSSD,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Client",
    )
    status = models.CharField(
        "Statut", max_length=20, choices=Status.choices, default=Status.EN_ATTENTE
    )
    total_amount = models.PositiveIntegerField("Montant total (XOF)", default=0)
    validation_code = models.CharField(
        "Code de validation", max_length=12, unique=True, blank=True
    )
    is_paid = models.BooleanField("Payée", default=False)
    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commande #{self.pk} - {self.total_amount} F - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Génère un code de validation unique à la création de la commande.
        if not self.validation_code:
            code = generate_validation_code()
            while Order.objects.filter(validation_code=code).exists():
                code = generate_validation_code()
            self.validation_code = code
        super().save(*args, **kwargs)

    def update_total(self):
        """Recalcule le montant total à partir des lignes de commande."""
        self.total_amount = sum(item.line_total for item in self.items.all())
        self.save(update_fields=["total_amount", "updated_at"])

    def valider_paiement(self):
        """Valide le paiement de la commande (agent au comptoir).

        Effets : statut -> PAYEE, is_paid -> True, et **décrément du stock** des
        produits commandés (décision de conception : le stock baisse au paiement,
        pas à la commande).

        Lève :
          - DejaPayeeError si la commande est déjà payée ;
          - StockInsuffisantError si le stock d'un produit est devenu insuffisant.

        L'opération est atomique : en cas d'erreur, rien n'est modifié.
        """
        with transaction.atomic():
            # Verrouille la commande pour éviter une double validation concurrente.
            order = Order.objects.select_for_update().get(pk=self.pk)
            if order.is_paid:
                raise DejaPayeeError(f"La commande #{order.pk} est déjà payée.")

            items = list(order.items.select_related("product"))

            # 1) Vérifier la disponibilité du stock pour toutes les lignes.
            for item in items:
                if item.quantity > item.product.stock:
                    raise StockInsuffisantError(
                        f"Stock insuffisant pour « {item.product.name} » "
                        f"(demandé {item.quantity}, disponible {item.product.stock})."
                    )

            # 2) Décrémenter le stock (décrément atomique via F()).
            for item in items:
                Product.objects.filter(pk=item.product_id).update(
                    stock=F("stock") - item.quantity
                )

            # 3) Marquer la commande comme payée.
            order.status = Order.Status.PAYEE
            order.is_paid = True
            order.save(update_fields=["status", "is_paid", "updated_at"])

        # Refléter le nouvel état sur l'instance appelante.
        self.status = Order.Status.PAYEE
        self.is_paid = True


class OrderItem(models.Model):
    """Ligne d'une commande : un produit, une quantité, un prix figé à l'achat."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Commande"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, verbose_name="Produit"
    )
    quantity = models.PositiveIntegerField("Quantité")
    # Prix unitaire copié au moment de l'achat (historisation : insensible aux
    # changements de prix ultérieurs du produit).
    unit_price = models.PositiveIntegerField("Prix unitaire (XOF)")
    line_total = models.PositiveIntegerField("Total ligne (XOF)", default=0)

    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def save(self, *args, **kwargs):
        # Le total de la ligne est toujours dérivé de quantité × prix unitaire.
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
