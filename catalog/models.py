from django.db import models


class Category(models.Model):
    """Catégorie de produits (ex. « Vivres », « Hygiène »)."""

    name = models.CharField("Nom", max_length=100, unique=True)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Produit vendu sur la plateforme. Prix exprimé en francs CFA (XOF, entier)."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,      # interdit de supprimer une catégorie utilisée
        related_name="products",
        verbose_name="Catégorie",
    )
    name = models.CharField("Nom", max_length=150)
    price = models.PositiveIntegerField("Prix (XOF)")
    stock = models.PositiveIntegerField("Stock", default=0)
    description = models.TextField("Description", blank=True)
    is_active = models.BooleanField("Actif", default=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["category__name", "name"]

    def __str__(self):
        return f"{self.name} - {self.price} F"

    @property
    def is_available(self):
        """Le produit est-il proposable au client USSD ?"""
        return self.is_active and self.stock > 0
