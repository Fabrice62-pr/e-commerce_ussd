from django.urls import path

from . import views

urlpatterns = [
    # Appelé par la passerelle USSD à chaque interaction
    path("callback/", views.ussd_callback, name="ussd-callback"),
]
