from django.contrib import admin

from .models import USSDSession


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    """Vue technique : utile pour déboguer les paniers en cours (Phase 3)."""

    list_display = ("session_id", "phone_number", "state", "updated_at")
    search_fields = ("session_id", "phone_number")
    readonly_fields = ("created_at", "updated_at")
