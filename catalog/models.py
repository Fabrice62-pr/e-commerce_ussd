from django.db import models

# Codes des langues traduites (doivent correspondre aux suffixes des champs `name_*`).
# Le français est la langue de référence : c'est le champ `name` lui-même.
TRANSLATED_LANGS = ("ha", "dyu", "ff", "wo")


class TranslatedNameMixin(models.Model):
    """Ajoute des noms traduits. Le champ `name` reste la référence (français).

    Si une traduction est vide, on retombe automatiquement sur le français.
    """

    name_ha = models.CharField("Nom (haoussa)", max_length=150, blank=True)
    name_dyu = models.CharField("Nom (dioula)", max_length=150, blank=True)
    name_ff = models.CharField("Nom (peul)", max_length=150, blank=True)
    name_wo = models.CharField("Nom (wolof)", max_length=150, blank=True)

    class Meta:
        abstract = True

    def get_name(self, lang="fr"):
        """Nom dans la langue demandée ; repli sur le français si non traduit."""
        if lang in TRANSLATED_LANGS:
            return getattr(self, f"name_{lang}", "") or self.name
        return self.name


class Category(TranslatedNameMixin):
    """Catégorie de produits (ex. « Vivres », « Hygiène »)."""

    name = models.CharField("Nom (français)", max_length=100, unique=True)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(TranslatedNameMixin):
    """Produit vendu sur la plateforme. Prix exprimé en francs CFA (XOF, entier)."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,      # interdit de supprimer une catégorie utilisée
        related_name="products",
        verbose_name="Catégorie",
    )
    name = models.CharField("Nom (français)", max_length=150)
    price = models.PositiveIntegerField("Prix (XOF)")
    stock = models.PositiveIntegerField("Stock", default=0)
    low_stock_threshold = models.PositiveIntegerField(
        "Seuil d'alerte stock bas",
        default=5,
        help_text="Une alerte s'affiche dans l'admin dès que le stock atteint ce seuil.",
    )
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

    @property
    def is_low_stock(self):
        """Le stock a-t-il atteint (ou dépassé) le seuil d'alerte ?"""
        return self.stock <= self.low_stock_threshold
