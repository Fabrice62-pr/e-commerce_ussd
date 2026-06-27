"""Webhook USSD : point d'entrée appelé par la passerelle (Africa's Talking).

La passerelle envoie une requête POST (form-encoded) avec notamment :
  - sessionId   : identifiant unique de la session
  - phoneNumber : numéro du client
  - text        : tout ce que le client a saisi depuis le début (segments séparés par '*')

On répond en texte brut commençant par "CON" (continuer) ou "END" (terminer).
"""
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .engine import process_ussd


@csrf_exempt  # la passerelle externe ne fournit pas de jeton CSRF
def ussd_callback(request):
    if request.method != "POST":
        return HttpResponse(
            "Point d'acces USSD. Utilisez une requete POST.",
            content_type="text/plain",
        )

    session_id = request.POST.get("sessionId", "")
    phone_number = request.POST.get("phoneNumber", "")
    text = request.POST.get("text", "")

    response = process_ussd(session_id, phone_number, text)
    return HttpResponse(response, content_type="text/plain")
