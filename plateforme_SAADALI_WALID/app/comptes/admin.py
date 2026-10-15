"""
Affichage des utilisateurs dans l'interface d'administration (/admin/).

On réutilise l'écran standard de Django, adapté à la connexion par e-mail
(il n'y a pas de champ « identifiant »).
"""

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group

from .models import Utilisateur

# Titres de l'administration (le bandeau, l'onglet du navigateur et l'accueil)
admin.site.site_header = "Administration"
admin.site.site_title = "Administration des stages"
admin.site.index_title = "Gérer les données de la plateforme"


class GroupeAdminReserve(GroupAdmin):
    """Les rôles (groupes) sont réservés à l'administrateur : le Career Center n'en a pas besoin
    et l'entrée « Authentification et autorisation » le perdait. Les rôles s'attribuent depuis la fiche d'un utilisateur."""

    def has_module_permission(self, request):
        return request.user.is_superuser


admin.site.unregister(Group)
admin.site.register(Group, GroupeAdminReserve)


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    # Colonnes de la liste des utilisateurs
    list_display = ("email", "last_name", "first_name", "liste_roles", "is_active")
    list_filter = ("groups", "is_active", "is_staff")
    search_fields = ("email", "last_name", "first_name")
    ordering = ("last_name", "first_name")
    filter_horizontal = ("groups",)   # choisir les rôles dans deux listes côte à côte (plus clair)
    list_per_page = 50

    # Écran de modification d'un utilisateur
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identité", {"fields": ("first_name", "last_name")}),
        ("Rôles et droits", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    # Écran de création d'un utilisateur
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2", "groups"),
        }),
    )

    @admin.display(description="Rôles")
    def liste_roles(self, utilisateur):
        return ", ".join(utilisateur.roles()) or "—"
