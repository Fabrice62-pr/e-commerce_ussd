from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .reports import get_rapport_data


@staff_member_required
def rapports(request):
    """Tableau de bord des rapports (réservé au personnel administrateur)."""
    context = {"data": get_rapport_data(), "title": "Rapports"}
    return render(request, "orders/rapports.html", context)
