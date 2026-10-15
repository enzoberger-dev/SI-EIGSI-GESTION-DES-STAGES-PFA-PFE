"""
Pages du Lot 4 « Pilotage et échanges » : imports et exports CSV, tableau de bord.
Toutes réservées au Career Center (rôle Service Stages).
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.views.decorators.cache import never_cache

from comptes import roles
from comptes.decorateurs import role_requis

import re

from django.http import HttpResponse
from django.utils import timezone

from .csv_outils import ErreurCSV
from .echanges import dossier_zip, exporter_conventions_signees, importer_moodle, importer_webaurion
from .models import Livrable, Stage, annee_universitaire_courante
from .pilotage import annees_disponibles, tableau_de_bord


@role_requis(roles.SERVICE_STAGES)
@never_cache  # la page peut afficher des mots de passe provisoires : jamais en cache
def import_webaurion(request):
    """US-08 : importer les étudiants et encadrants depuis un CSV exporté de WebAurion."""
    rapport = None
    if request.method == "POST":
        fichier = request.FILES.get("fichier")
        if fichier is None:
            messages.error(request, "Choisissez un fichier CSV.")
        else:
            try:
                rapport = importer_webaurion(fichier.read(), simuler="simuler" in request.POST)
            except ErreurCSV as erreur:
                messages.error(request, str(erreur))
    return render(request, "stages/import_webaurion.html", {"rapport": rapport})


@role_requis(roles.SERVICE_STAGES)
def export_conventions(request):
    """US-07 : télécharger les conventions signées au format WebAurion. Année : ?annee=2026-2027
    (par défaut l'année en cours). Le nom du fichier est horodaté."""
    annee = request.GET.get("annee", "")
    if not re.fullmatch(r"\d{4}-\d{4}", annee):
        annee = annee_universitaire_courante()
    contenu, _nb = exporter_conventions_signees(annee)
    reponse = HttpResponse(contenu, content_type="text/csv; charset=utf-8")
    horodatage = timezone.localtime().strftime("%Y%m%d-%H%M")
    reponse["Content-Disposition"] = f'attachment; filename="conventions-signees-{annee}-{horodatage}.csv"'
    return reponse


@role_requis(roles.SERVICE_STAGES)
def tableau(request):
    """US-11 : tableau de bord des stages. Année : ?annee=2026-2027 (par défaut l'année en cours).
    Les chiffres sont recalculés à chaque affichage ; la page se recharge seule toutes les minutes."""
    annees = annees_disponibles()
    annee = request.GET.get("annee")
    if annee not in annees:
        annee = annee_universitaire_courante()
    return render(request, "stages/tableau_de_bord.html", {
        "donnees": tableau_de_bord(annee), "annees": annees,
    })


@role_requis(roles.SERVICE_STAGES)
def import_moodle(request):
    """Importer l'export d'un devoir Moodle : les livrables remis passent « rendus » sans saisie à la main."""
    noms = list(Livrable.objects.order_by("nom").values_list("nom", flat=True).distinct())
    rapport = None
    if request.method == "POST":
        fichier = request.FILES.get("fichier")
        nom = request.POST.get("livrable", "")
        if fichier is None:
            messages.error(request, "Choisissez un fichier CSV.")
        elif nom not in noms:
            messages.error(request, "Choisissez le livrable auquel correspond ce devoir Moodle.")
        else:
            try:
                rapport = importer_moodle(fichier.read(), nom, par=request.user, simuler="simuler" in request.POST)
            except ErreurCSV as erreur:
                messages.error(request, str(erreur))
    return render(request, "stages/import_moodle.html", {"rapport": rapport, "noms": noms})


@role_requis(roles.SERVICE_STAGES)
def dossier_stage(request, stage_pk):
    """Télécharge le dossier complet d'un stage (convention, scan signé, historique) en ZIP."""
    stage = get_object_or_404(Stage.objects.select_related("etudiant", "promotion", "entreprise"), pk=stage_pk)
    nom = slugify(stage.etudiant.get_full_name()) or f"stage-{stage.pk}"
    reponse = HttpResponse(dossier_zip(stage), content_type="application/zip")
    reponse["Content-Disposition"] = f'attachment; filename="dossier-{nom}-{stage.promotion.annee_universitaire}.zip"'
    return reponse
