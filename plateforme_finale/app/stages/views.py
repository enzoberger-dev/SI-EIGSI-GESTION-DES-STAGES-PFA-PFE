"""
Pages du suivi des stages.
"""

import datetime
import mimetypes
import os

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from comptes import roles
from comptes.decorateurs import role_requis

from . import frise
from .forms import AffectationForm, DecisionForm, StageForm
from .models import (
    ANNEE_VALIDATION_PAR_ENCADRANT, Affectation, Convention, Historique, Inscription, Livrable, Stage,
    annee_universitaire_courante,
)
from .services import (
    STATUTS_MODIFIABLES, affecter_encadrant, annuler_rendu, aujourdhui, convention_en_vigueur,
    decider_stage, deposer_scan, generer_convention, marquer_envoyee, marquer_rendu, prolonger_livrable,
    refuser_scan, soumettre_stage, valider_signature,
)


# ---------------------------------------------------------------------------
# Career Center
# ---------------------------------------------------------------------------

def etudiants_a_encadrer(annee):
    """Étudiants inscrits en 4e ou 5e année pour l'année donnée."""
    return get_user_model().objects.filter(
        inscriptions__annee_universitaire=annee,
        inscriptions__promotion__annee_etudes__gte=ANNEE_VALIDATION_PAR_ENCADRANT,
    ).distinct()


@role_requis(roles.SERVICE_STAGES)
def affectations(request):
    """US-23 : le Career Center affecte (ou change) l'encadrant des étudiants de 4e et 5e année."""
    annee = annee_universitaire_courante()
    etudiants = etudiants_a_encadrer(annee)

    if request.method == "POST":
        form = AffectationForm(request.POST, etudiants_possibles=etudiants)
        if form.is_valid():
            etudiant = form.cleaned_data["etudiant"]
            encadrant = form.cleaned_data["encadrant"]
            affecter_encadrant(etudiant, encadrant, par=request.user, annee=annee)
            messages.success(
                request,
                f"{encadrant.get_full_name()} encadre désormais {etudiant.get_full_name()}.",
            )
        else:
            messages.error(request, "Choisissez un encadrant dans la liste.")
        return redirect("affectations")

    # Encadrant actuel de chaque étudiant
    actives = {
        a.etudiant_id: a
        for a in Affectation.objects.filter(annee_universitaire=annee, active=True).select_related("encadrant")
    }
    lignes = []
    for etudiant in etudiants.order_by("last_name", "first_name"):
        inscription = etudiant.inscriptions.get(annee_universitaire=annee)
        affectation = actives.get(etudiant.id)
        lignes.append({
            "etudiant": etudiant,
            "promotion": inscription.promotion,
            "encadrant": affectation.encadrant if affectation else None,
            "form": AffectationForm(
                initial={"etudiant": etudiant, "encadrant": affectation.encadrant if affectation else None},
                etudiants_possibles=etudiants,
            ),
        })
    # Étudiants sans encadrant en premier : ce sont eux qu'il faut traiter
    lignes.sort(key=lambda ligne: ligne["encadrant"] is not None)

    derniers_changements = (
        Affectation.objects.filter(annee_universitaire=annee)
        .select_related("etudiant", "encadrant", "affecte_par")[:10]
    )
    return render(request, "stages/affectations.html", {
        "annee": annee,
        "lignes": lignes,
        "nb_sans_encadrant": sum(1 for ligne in lignes if ligne["encadrant"] is None),
        "derniers_changements": derniers_changements,
    })


# ---------------------------------------------------------------------------
# Étudiant
# ---------------------------------------------------------------------------

def inscription_courante(etudiant):
    """Inscription de l'étudiant pour l'année en cours (ou None)."""
    return (
        Inscription.objects.filter(etudiant=etudiant, annee_universitaire=annee_universitaire_courante())
        .select_related("promotion").first()
    )


@role_requis(roles.ETUDIANT)
def mon_stage(request):
    """US-01 / E3 : l'étudiant voit sa fiche, son statut et l'historique de son dossier."""
    inscription = inscription_courante(request.user)
    stage = None
    if inscription:
        stage = Stage.objects.filter(etudiant=request.user, promotion=inscription.promotion).first()
    modifiable = stage is None or stage.statut in STATUTS_MODIFIABLES
    convention = convention_en_vigueur(stage) if stage else None
    livrables = list(stage.livrables.select_related("modele").all()) if stage else []
    soutenance = getattr(stage, "soutenance", None) if stage else None  # None si pas encore créée
    etapes, action = frise.calculer(stage, convention, livrables, soutenance)
    return render(request, "stages/mon_stage.html", {
        "inscription": inscription,
        "stage": stage,
        "frise": etapes,
        "action": action,
        "modifiable": modifiable,
        "historique": stage.historique.select_related("auteur") if stage else [],
        "a_completer": stage.erreurs_soumission() if stage and modifiable else [],
        "valideur": stage.valideur() if stage else None,
        "convention": convention,
        "livrables": livrables,
        "aujourdhui": aujourdhui(),
    })


@role_requis(roles.ETUDIANT)
def modifier_mon_stage(request):
    """US-01 / E1 : déclarer ou corriger sa fiche, l'enregistrer en brouillon ou la soumettre."""
    inscription = inscription_courante(request.user)
    if inscription is None:
        messages.error(request, "Vous n'êtes inscrit dans aucune promotion cette année : contactez le Career Center.")
        return redirect("mon_stage")

    stage = Stage.objects.filter(etudiant=request.user, promotion=inscription.promotion).first()
    if stage is None:
        stage = Stage(etudiant=request.user, promotion=inscription.promotion)
    elif stage.statut not in STATUTS_MODIFIABLES:
        messages.error(request, "Votre fiche a déjà été soumise : elle ne peut plus être modifiée.")
        return redirect("mon_stage")

    if request.method == "POST":
        form = StageForm(request.POST, instance=stage)
        if form.is_valid():
            creation = stage.pk is None
            stage = form.save()
            if creation:
                Historique.objects.create(stage=stage, auteur=request.user, action=Historique.Action.CREATION)

            if "soumettre" in request.POST:
                erreurs = soumettre_stage(stage, par=request.user)
                if erreurs:
                    # La fiche est enregistrée, mais reste modifiable : on affiche ce qui manque
                    for erreur in erreurs:
                        messages.error(request, erreur)
                    return redirect("modifier_mon_stage")
                messages.success(request, "Votre fiche a été soumise. Vous serez prévenu de la décision.")
            else:
                messages.success(request, "Brouillon enregistré.")
            return redirect("mon_stage")
    else:
        form = StageForm(instance=stage)

    return render(request, "stages/fiche_form.html", {
        "form": form,
        "stage": stage,
        "promotion": inscription.promotion,
    })


# ---------------------------------------------------------------------------
# Valideur : encadrant (4e, 5e année) ou coordinateur de promotion (1re à 3e)
# ---------------------------------------------------------------------------

@role_requis(roles.ENCADRANT, roles.COORDINATEUR)
def stages_a_valider(request):
    """US-02 / E2 : les fiches soumises dont la personne connectée est le valideur."""
    soumis = Stage.objects.filter(statut=Stage.Statut.SOUMIS).select_related(
        "etudiant", "entreprise", "promotion"
    ).order_by("modifie_le")
    a_traiter = [stage for stage in soumis if stage.valideur() == request.user]
    mes_decisions = (
        Historique.objects.filter(
            auteur=request.user, action__in=[Historique.Action.VALIDATION, Historique.Action.REFUS]
        ).select_related("stage__etudiant", "stage__entreprise").order_by("-date")[:10]
    )
    return render(request, "stages/a_valider.html", {
        "a_traiter": a_traiter,
        "mes_decisions": mes_decisions,
    })


@role_requis(roles.ENCADRANT, roles.COORDINATEUR)
def decider(request, pk):
    """US-02 / E2 : fiche détaillée et décision (valider, ou refuser avec motif)."""
    stage = get_object_or_404(
        Stage.objects.select_related("etudiant", "entreprise", "promotion"), pk=pk
    )
    # Seul le valideur de CE stage peut le voir ici (pas les autres encadrants)
    if stage.valideur() != request.user:
        raise PermissionDenied("Vous n'êtes pas le valideur de ce stage.")

    if request.method == "POST" and stage.statut == Stage.Statut.SOUMIS:
        form = DecisionForm(request.POST)
        if form.is_valid():
            valider = form.cleaned_data["decision"] == "valider"
            erreurs = decider_stage(stage, par=request.user, valider=valider, motif=form.cleaned_data["motif"])
            if not erreurs:
                nom = stage.etudiant.get_full_name()
                messages.success(request, f"Stage de {nom} {'validé' if valider else 'refusé'}. L'étudiant est prévenu.")
                return redirect("stages_a_valider")
            for erreur in erreurs:
                messages.error(request, erreur)
    else:
        form = DecisionForm()

    return render(request, "stages/decision.html", {
        "stage": stage,
        "form": form,
        "historique": stage.historique.select_related("auteur"),
        "en_attente": stage.statut == Stage.Statut.SOUMIS,
    })


# ---------------------------------------------------------------------------
# Convention (Lot 2)
# ---------------------------------------------------------------------------

@role_requis(roles.SERVICE_STAGES)
def conventions(request):
    """Career Center : stages validés à mettre en convention, conventions en cours, conventions signées."""
    a_generer = [
        stage for stage in Stage.objects.filter(statut=Stage.Statut.VALIDE)
        .select_related("etudiant", "entreprise", "promotion").order_by("modifie_le")
        if convention_en_vigueur(stage) is None
    ]
    en_vigueur = Convention.objects.exclude(statut=Convention.Statut.REMPLACEE).select_related(
        "stage__etudiant", "stage__entreprise", "stage__promotion"
    )
    return render(request, "stages/conventions.html", {
        "a_generer": a_generer,
        "a_faire_signer": en_vigueur.filter(statut=Convention.Statut.GENEREE),
        "chez_etudiant": en_vigueur.filter(statut=Convention.Statut.ENVOYEE),
        "signees": en_vigueur.filter(statut=Convention.Statut.SIGNEE).order_by("-signee_le")[:20],
    })


def _resultat(request, erreurs, succes):
    """Affiche le message de succès, ou les erreurs, puis revient à la page des conventions."""
    if erreurs:
        for erreur in erreurs:
            messages.error(request, erreur)
    else:
        messages.success(request, succes)
    return redirect("conventions")


@role_requis(roles.SERVICE_STAGES)
@require_POST
def convention_generer(request, stage_pk):
    stage = get_object_or_404(Stage, pk=stage_pk)
    convention, erreurs = generer_convention(stage, par=request.user)
    return _resultat(request, erreurs, f"Convention n° {convention.numero if convention else ''} générée.")


@role_requis(roles.SERVICE_STAGES)
@require_POST
def convention_envoyer(request, pk):
    convention = get_object_or_404(Convention, pk=pk)
    erreurs = marquer_envoyee(convention, par=request.user)
    return _resultat(request, erreurs, f"Convention n° {convention.numero} envoyée à l'étudiant.")


@role_requis(roles.SERVICE_STAGES)
@require_POST
def convention_valider(request, pk):
    convention = get_object_or_404(Convention, pk=pk)
    erreurs = valider_signature(convention, par=request.user)
    return _resultat(request, erreurs, f"Convention n° {convention.numero} signée par toutes les parties.")


@role_requis(roles.SERVICE_STAGES)
@require_POST
def convention_refuser_scan(request, pk):
    convention = get_object_or_404(Convention, pk=pk)
    erreurs = refuser_scan(convention, par=request.user, motif=request.POST.get("motif", ""))
    return _resultat(request, erreurs, "Scan refusé : l'étudiant est prévenu.")


@role_requis(roles.ETUDIANT)
@require_POST
def deposer_scan_convention(request):
    """L'étudiant dépose le scan de sa convention signée par les trois parties."""
    inscription = inscription_courante(request.user)
    stage = Stage.objects.filter(etudiant=request.user, promotion=inscription.promotion).first() if inscription else None
    convention = convention_en_vigueur(stage) if stage else None
    if convention is None:
        messages.error(request, "Vous n'avez pas de convention en cours.")
    elif "scan" not in request.FILES:
        messages.error(request, "Choisissez le fichier du scan.")
    else:
        erreurs = deposer_scan(convention, request.FILES["scan"], par=request.user)
        if erreurs:
            for erreur in erreurs:
                messages.error(request, erreur)
        else:
            messages.success(request, "Scan déposé. Le Career Center va le vérifier.")
    return redirect("mon_stage")


@role_requis(roles.SERVICE_STAGES, roles.ETUDIANT)
def telecharger_convention(request, pk, quoi):
    """Téléchargement protégé : seul le Career Center et l'étudiant concerné peuvent récupérer
    le PDF ou le scan. Les fichiers ne sont jamais servis directement."""
    convention = get_object_or_404(Convention.objects.select_related("stage"), pk=pk)
    est_career_center = request.user.a_le_role(roles.SERVICE_STAGES)
    if not est_career_center and convention.stage.etudiant_id != request.user.id:
        raise PermissionDenied("Cette convention n'est pas la vôtre.")
    fichier = {"pdf": convention.fichier_pdf, "scan": convention.scan_signe}.get(quoi)
    if fichier is None or not fichier:
        raise Http404("Fichier introuvable.")
    type_mime = mimetypes.guess_type(fichier.name)[0] or "application/octet-stream"
    return FileResponse(
        fichier.open("rb"), as_attachment=True, filename=os.path.basename(fichier.name), content_type=type_mime
    )


# ---------------------------------------------------------------------------
# Suivi des livrables rendus sur Moodle (Lot 3 bis)
# ---------------------------------------------------------------------------

@role_requis(roles.SERVICE_STAGES)
def suivi(request):
    """Career Center : tous les livrables, les retards, et le marquage « rendu ». Filtre : ?retard=1."""
    livrables = Livrable.objects.select_related("stage__etudiant", "stage__promotion").prefetch_related("rappels")
    aujourdhui_ = aujourdhui()
    lignes = []
    for livrable in livrables:
        en_retard = livrable.statut == Livrable.Statut.A_RENDRE and livrable.date_limite < aujourdhui_
        lignes.append({"livrable": livrable, "en_retard": en_retard, "nb_rappels": len(livrable.rappels.all())})
    nb_retards = sum(1 for ligne in lignes if ligne["en_retard"])
    seulement_retards = request.GET.get("retard") == "1"
    if seulement_retards:
        lignes = [ligne for ligne in lignes if ligne["en_retard"]]
    return render(request, "stages/suivi.html", {
        "lignes": lignes, "seulement_retards": seulement_retards, "nb_retards": nb_retards,
    })


@role_requis(roles.SERVICE_STAGES)
@require_POST
def livrable_rendu(request, pk):
    """Le Career Center marque un livrable comme rendu sur Moodle (ou annule cette marque)."""
    livrable = get_object_or_404(Livrable, pk=pk)
    if request.POST.get("action") == "annuler":
        erreurs = annuler_rendu(livrable, par=request.user)
        succes = f"« {livrable.nom} » est de nouveau « à rendre »."
    else:
        erreurs = marquer_rendu(livrable, par=request.user)
        succes = f"« {livrable.nom} » marqué comme rendu : les rappels s'arrêtent."
    for erreur in erreurs:
        messages.error(request, erreur)
    if not erreurs:
        messages.success(request, succes)
    return redirect("suivi")


@role_requis(roles.SERVICE_STAGES)
@require_POST
def livrable_prolonger(request, pk):
    """Le Career Center repousse la date limite d'un livrable."""
    livrable = get_object_or_404(Livrable, pk=pk)
    try:
        nouvelle_date = datetime.date.fromisoformat(request.POST.get("date", ""))
    except ValueError:
        messages.error(request, "Date invalide.")
        return redirect("suivi")
    erreurs = prolonger_livrable(livrable, nouvelle_date, par=request.user)
    if erreurs:
        for erreur in erreurs:
            messages.error(request, erreur)
    else:
        messages.success(request, f"Date limite de « {livrable.nom} » repoussée au {nouvelle_date:%d/%m/%Y}.")
    return redirect("suivi")
