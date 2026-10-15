"""
Écrans d'administration (/admin/) pour le Career Center : promotions,
inscriptions, affectations, entreprises et fiches de stage.
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import (
    Affectation, Convention, Entreprise, Historique, Inscription, Livrable, ModeleLivrable,
    ParametresEcole, Promotion, Relance, Stage,
)


class InscriptionEnLigne(admin.TabularInline):
    """Inscrire les étudiants directement depuis la page d'une promotion."""
    model = Inscription
    extra = 1
    autocomplete_fields = ["etudiant"]


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "coordinateur", "nombre_inscrits")
    list_filter = ("annee_universitaire", "annee_etudes")
    list_select_related = ("coordinateur",)
    autocomplete_fields = ["coordinateur"]
    inlines = [InscriptionEnLigne]

    @admin.display(description="Inscrits")
    def nombre_inscrits(self, promotion):
        return promotion.inscriptions.count()


@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "encadrant", "annee_universitaire", "active", "date_affectation")
    list_filter = ("annee_universitaire", "active")
    search_fields = ("etudiant__email", "etudiant__last_name", "encadrant__last_name")
    autocomplete_fields = ["etudiant", "encadrant"]


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ("raison_sociale", "ville", "pays", "email_contact", "telephone")
    search_fields = ("raison_sociale", "ville", "email_contact")
    list_filter = ("pays",)


class HistoriqueEnLigne(admin.TabularInline):
    """Le fil du dossier, affiché en lecture seule sous la fiche."""
    model = Historique
    extra = 0
    can_delete = False
    readonly_fields = ("date", "action", "auteur", "commentaire")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ParametresEcole)
class ParametresEcoleAdmin(admin.ModelAdmin):
    """Une seule ligne : les informations de l'école reprises dans la convention."""

    fieldsets = (
        ("L'école", {"fields": ("nom", "sigle", "cursus", "adresse", "site_web", "telephone")}),
        ("Signataires de la convention", {"fields": ("representant", "directeur_etudes")}),
        ("Contact du Career Center", {"fields": ("email_contact",)}),
        ("Rappels et relances automatiques", {
            "fields": ("rappels_avant", "rappels_apres", "relances_delais"),
            "description": "Nombres de jours séparés par des virgules (exemple : 7, 3, 1).",
        }),
    )

    def changelist_view(self, request, extra_context=None):
        """Il n'y a qu'une seule ligne : on ouvre directement sa fiche au lieu d'une liste d'un élément."""
        parametres = ParametresEcole.objects.first()
        if parametres is not None and self.has_view_or_change_permission(request, parametres):
            return redirect(reverse("admin:stages_parametresecole_change", args=[parametres.pk]))
        return super().changelist_view(request, extra_context)

    def has_add_permission(self, request):
        return not ParametresEcole.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Convention)
class ConventionAdmin(admin.ModelAdmin):
    """Consultation seulement : les conventions se gèrent depuis l'écran « Conventions »."""
    list_display = ("numero", "version", "stage", "statut", "cree_le", "signee_le")
    list_filter = ("statut",)
    search_fields = ("numero", "stage__etudiant__last_name", "stage__etudiant__email")
    readonly_fields = [champ.name for champ in Convention._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ModeleLivrable)
class ModeleLivrableAdmin(admin.ModelAdmin):
    """Livrables attendus par type de stage, calcul de leur date limite et lien du devoir Moodle."""
    list_display = ("type_stage", "nom", "est_rapport", "calcul", "mois", "jour", "jours", "lien_moodle", "ordre")
    list_filter = ("type_stage",)


@admin.register(Livrable)
class LivrableAdmin(admin.ModelAdmin):
    """Consultation seulement : les livrables se suivent depuis l'écran « Suivi »."""
    list_display = ("nom", "stage", "date_limite", "statut")
    list_filter = ("statut",)
    readonly_fields = [champ.name for champ in Livrable._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "promotion", "entreprise", "statut", "date_debut", "date_fin")
    list_filter = ("statut", "promotion__annee_universitaire", "promotion__annee_etudes")
    search_fields = ("etudiant__last_name", "etudiant__first_name", "etudiant__email", "entreprise__raison_sociale", "sujet")
    list_select_related = ("etudiant", "promotion", "entreprise")
    list_per_page = 50
    autocomplete_fields = ["etudiant", "entreprise"]
    readonly_fields = ("cree_le", "modifie_le")
    inlines = [HistoriqueEnLigne]

    # La fiche est longue : on la découpe dans l'ordre de la convention
    fieldsets = (
        ("Étudiant et promotion", {"fields": ("etudiant", "promotion", "statut")}),
        ("Entreprise et sujet", {"fields": ("entreprise", "origine", "sujet", "lieu_si_different")}),
        ("Représentant et tuteur", {"fields": (
            "representant_nom", "representant_fonction", "tuteur_nom", "tuteur_email", "tuteur_telephone")}),
        ("Durée et horaires", {"fields": (
            "date_debut", "date_fin", "heures_max_semaine", "horaires", "cas_particuliers", "date_limite_rapport")}),
        ("Gratification", {"classes": ("collapse",), "fields": (
            "gratification_montant", "gratification_modalites", "avantages_nature")}),
        ("Dates de la fiche", {"classes": ("collapse",), "fields": ("cree_le", "modifie_le")}),
    )


@admin.register(Relance)
class RelanceAdmin(admin.ModelAdmin):
    """Consultation seulement : les relances partent toutes seules (commande envoyer_relances)."""
    list_display = ("envoye_le", "type", "stage", "delai", "destinataire")
    list_filter = ("type",)
    readonly_fields = [champ.name for champ in Relance._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
