"""
Pages des soutenances (Lot 6).

- Career Center : créer une campagne, voir les réponses des jurys, proposer et valider le planning,
  corriger un créneau, valider les PV et exporter les notes.
- Jury : répondre au sondage de disponibilités, voir ses soutenances, saisir le PV et la note.
"""

import re
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from comptes import roles
from comptes.decorateurs import role_requis
from stages.models import annee_universitaire_courante

from .forms import CampagneForm
from .models import Campagne, Disponibilite, ReponseJury, Salle, Soutenance
from .services import (
    deplacer_soutenance, enregistrer_disponibilites, exporter_notes, jurys_sans_reponse, membres_du_jury,
    ouvrir_campagne, proposer_planning, refuser_pv, saisir_pv, valider_pv, valider_planning,
)

FORMAT_CRENEAU = "%Y-%m-%dT%H:%M"


def _afficher(request, erreurs, succes):
    """Messages de résultat : les erreurs s'il y en a, sinon le succès."""
    if erreurs:
        for erreur in erreurs:
            messages.error(request, erreur)
    else:
        messages.success(request, succes)


# ---------------------------------------------------------------------------
# Career Center
# ---------------------------------------------------------------------------

@role_requis(roles.SERVICE_STAGES)
def liste(request):
    """Les campagnes de soutenances, et le formulaire pour en créer une (les jurys sont prévenus par e-mail)."""
    if request.method == "POST":
        form = CampagneForm(request.POST)
        if form.is_valid():
            campagne = form.save()
            nb = ouvrir_campagne(campagne)
            messages.success(request, f"Campagne créée : {nb} membre(s) du jury prévenu(s) par e-mail.")
            return redirect("soutenances_campagne", pk=campagne.pk)
    else:
        form = CampagneForm(initial={"annee_universitaire": annee_universitaire_courante()})
    return render(request, "soutenances/liste.html", {
        "campagnes": Campagne.objects.all(), "form": form,
        "nb_salles": Salle.objects.filter(active=True).count(), "nb_jury": membres_du_jury().count(),
    })


@role_requis(roles.SERVICE_STAGES)
def campagne(request, pk):
    """Une campagne : réponses des jurys, planning, PV à valider."""
    campagne = get_object_or_404(Campagne, pk=pk)
    soutenances = list(
        campagne.soutenances.select_related("stage__etudiant", "stage__entreprise", "stage__promotion", "salle")
        .prefetch_related("jury")
    )
    return render(request, "soutenances/campagne.html", {
        "campagne": campagne,
        "soutenances": soutenances,
        "a_valider": [s for s in soutenances if s.statut == Soutenance.Statut.PV_SAISI],
        "nb_proposees": sum(1 for s in soutenances if s.statut == Soutenance.Statut.PROPOSEE),
        "reponses": ReponseJury.objects.filter(campagne=campagne).count(),
        "sans_reponse": jurys_sans_reponse(campagne),
        "nb_jury": membres_du_jury().count(),
        "salles": Salle.objects.filter(active=True),
        "jury": membres_du_jury(),
    })


@role_requis(roles.SERVICE_STAGES)
@require_POST
def proposer(request, pk):
    campagne = get_object_or_404(Campagne, pk=pk)
    resultat = proposer_planning(campagne)
    for erreur in resultat["erreurs"]:
        messages.error(request, erreur)
    if not resultat["erreurs"]:
        messages.success(
            request, f"{resultat['planifiees']} soutenance(s) planifiée(s) : relisez, corrigez si besoin, puis validez.")
        for s in resultat["non_planifiables"]:
            messages.error(
                request,
                f"Aucun créneau possible pour {s.stage.etudiant.get_full_name() or s.stage.etudiant.email} "
                f"(disponibilités des jurys, salles ou dates insuffisantes).",
            )
    return redirect("soutenances_campagne", pk=pk)


@role_requis(roles.SERVICE_STAGES)
@require_POST
def valider(request, pk):
    campagne = get_object_or_404(Campagne, pk=pk)
    _afficher(request, valider_planning(campagne, par=request.user), "Planning validé : les convocations sont parties.")
    return redirect("soutenances_campagne", pk=pk)


@role_requis(roles.SERVICE_STAGES)
@require_POST
def deplacer(request, pk):
    """Fixer ou corriger à la main le créneau, la salle et le jury d'une soutenance."""
    soutenance = get_object_or_404(Soutenance.objects.select_related("campagne", "stage__etudiant"), pk=pk)
    try:
        debut = timezone.make_aware(datetime.strptime(request.POST.get("debut", ""), FORMAT_CRENEAU))
    except ValueError:
        messages.error(request, "Date et heure invalides.")
        return redirect("soutenances_campagne", pk=soutenance.campagne_id)
    salle = Salle.objects.filter(pk=request.POST.get("salle") or 0, active=True).first()
    if salle is None:
        messages.error(request, "Choisissez une salle.")
        return redirect("soutenances_campagne", pk=soutenance.campagne_id)
    membres = get_user_model().objects.filter(pk__in=[p for p in request.POST.getlist("jury") if p.isdigit()])
    _afficher(request, deplacer_soutenance(soutenance, debut, salle, membres, par=request.user), "Soutenance enregistrée.")
    return redirect("soutenances_campagne", pk=soutenance.campagne_id)


@role_requis(roles.SERVICE_STAGES)
@require_POST
def pv_valider(request, pk):
    soutenance = get_object_or_404(Soutenance, pk=pk)
    _afficher(request, valider_pv(soutenance, par=request.user), "PV et note validés.")
    return redirect("soutenances_campagne", pk=soutenance.campagne_id)


@role_requis(roles.SERVICE_STAGES)
@require_POST
def pv_refuser(request, pk):
    soutenance = get_object_or_404(Soutenance, pk=pk)
    _afficher(request, refuser_pv(soutenance, par=request.user, motif=request.POST.get("motif", "")),
              "PV renvoyé au jury pour correction.")
    return redirect("soutenances_campagne", pk=soutenance.campagne_id)


@role_requis(roles.SERVICE_STAGES)
def export_notes(request):
    """US-16 : télécharger les notes validées (CSV pour WebAurion). Année : ?annee=2026-2027."""
    annee = request.GET.get("annee", "")
    if not re.fullmatch(r"\d{4}-\d{4}", annee):
        annee = annee_universitaire_courante()
    contenu, _nb = exporter_notes(annee)
    reponse = HttpResponse(contenu, content_type="text/csv; charset=utf-8")
    horodatage = timezone.localtime().strftime("%Y%m%d-%H%M")
    reponse["Content-Disposition"] = f'attachment; filename="notes-soutenances-{annee}-{horodatage}.csv"'
    return reponse


# ---------------------------------------------------------------------------
# Jury
# ---------------------------------------------------------------------------

@role_requis(roles.JURY)
def jury_accueil(request):
    """Espace du jury : sondages à remplir et soutenances à venir ou à documenter."""
    repondues = set(ReponseJury.objects.filter(membre=request.user).values_list("campagne_id", flat=True))
    sondages = Campagne.objects.filter(statut=Campagne.Statut.OUVERTE)
    mes_soutenances = request.user.soutenances_jury.exclude(debut=None).select_related(
        "stage__etudiant", "stage__entreprise", "salle", "campagne").prefetch_related("jury").order_by("debut")
    return render(request, "soutenances/jury_accueil.html", {
        "sondages": [{"campagne": c, "repondu": c.pk in repondues} for c in sondages],
        "soutenances": mes_soutenances,
    })


@role_requis(roles.JURY)
def jury_disponibilites(request, pk):
    """US-12 : cocher les créneaux où l'on est disponible."""
    campagne = get_object_or_404(Campagne, pk=pk)
    creneaux = campagne.creneaux()
    par_cle = {timezone.localtime(c).strftime(FORMAT_CRENEAU): c for c in creneaux}

    if request.method == "POST":
        choisis = [par_cle[cle] for cle in request.POST.getlist("creneau") if cle in par_cle]
        erreurs = enregistrer_disponibilites(campagne, request.user, choisis)
        _afficher(request, erreurs, f"Merci : {len(choisis)} créneau(x) enregistré(s). "
                                    f"Vous pouvez modifier votre réponse tant que la campagne est ouverte.")
        return redirect("jury_disponibilites", pk=pk)

    cochees = set(Disponibilite.objects.filter(campagne=campagne, membre=request.user).values_list("debut", flat=True))
    jours = {}
    for c in creneaux:
        local = timezone.localtime(c)
        jours.setdefault(local.date(), []).append(
            {"cle": local.strftime(FORMAT_CRENEAU), "heure": local, "coche": c in cochees})
    return render(request, "soutenances/disponibilites.html", {
        "campagne": campagne, "jours": jours, "ouverte": campagne.statut == Campagne.Statut.OUVERTE,
        "a_repondu": ReponseJury.objects.filter(campagne=campagne, membre=request.user).exists(),
    })


@role_requis(roles.JURY)
def jury_pv(request, pk):
    """US-15 : saisir le procès-verbal et la note d'une soutenance dont on est membre du jury."""
    soutenance = get_object_or_404(
        Soutenance.objects.select_related("stage__etudiant", "stage__entreprise", "salle").prefetch_related("jury"),
        pk=pk)
    if not soutenance.jury.filter(pk=request.user.pk).exists():
        raise PermissionDenied("Vous n'êtes pas membre du jury de cette soutenance.")
    if request.method == "POST":
        erreurs = saisir_pv(soutenance, request.user, request.POST.get("note", ""), request.POST.get("pv", ""))
        if not erreurs:
            messages.success(request, "PV et note enregistrés : le Career Center va les valider.")
            return redirect("jury_accueil")
        for erreur in erreurs:
            messages.error(request, erreur)
    modifiable = soutenance.statut in (Soutenance.Statut.CONVOQUEE, Soutenance.Statut.PV_SAISI)
    saisie = request.POST if request.method == "POST" else {
        "note": str(soutenance.note).replace(".", ",") if soutenance.note is not None else "", "pv": soutenance.pv}
    return render(request, "soutenances/pv.html", {
        "soutenance": soutenance, "modifiable": modifiable, "saisie": saisie,
        "dernier_renvoi": soutenance.stage.historique.filter(action="PV_REFUSE").order_by("-date").first(),
    })
