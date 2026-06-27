from django.db import models


class USSDSession(models.Model):
    """État d'une session USSD en cours.

    L'USSD est « sans état » : à chaque touche pressée, la passerelle nous renvoie
    tout l'historique saisi. On stocke malgré tout le panier ici pour qu'il survive
    aux délais d'expiration de session (le client peut recomposer le code et
    retrouver son panier).
    """

    session_id = models.CharField("ID de session", max_length=100, unique=True)
    phone_number = models.CharField("Numéro de téléphone", max_length=20)
    # Panier : liste d'articles, ex. [{"product_id": 1, "qty": 2}, ...]
    cart = models.JSONField("Panier", default=list, blank=True)
    state = models.CharField("Écran courant", max_length=50, blank=True)
    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "Session USSD"
        verbose_name_plural = "Sessions USSD"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Session {self.session_id} ({self.phone_number})"
