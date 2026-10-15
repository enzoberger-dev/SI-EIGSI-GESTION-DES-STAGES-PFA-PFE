"""
Administration (/admin/) des soutenances : le Career Center gère les salles ; le reste se fait depuis
les écrans « Soutenances » (consultation seulement ici).
"""

from django.contrib import admin

from .models import Campagne, Salle, Soutenance


@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):
    list_display = ("nom", "active")
    list_filter = ("active",)


@admin.register(Campagne)
class CampagneAdmin(admin.ModelAdmin):
    """Consultation seulement : les campagnes se créent et se pilotent depuis l'écran « Soutenances »."""
    list_display = ("nom", "annee_universitaire", "date_debut", "date_fin", "statut")
    readonly_fields = [champ.name for champ in Campagne._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Soutenance)
class SoutenanceAdmin(admin.ModelAdmin):
    """Consultation seulement : voir l'écran « Soutenances »."""
    list_display = ("__str__", "debut", "salle", "statut", "note")
    list_filter = ("statut", "campagne")
    readonly_fields = [champ.name for champ in Soutenance._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
