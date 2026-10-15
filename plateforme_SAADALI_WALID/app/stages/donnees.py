"""
Protection des données personnelles (Lot 7, loi marocaine 09-08).

- donnees_personnelles : tout ce que la plateforme détient sur une personne (droit d'ACCÈS) ;
- anciens_comptes / anonymiser : comptes d'étudiants dont le dossier a dépassé la durée de conservation
  (10 ans après la dernière année d'inscription, comme dans l'article 13 de la convention). L'anonymisation
  remplace le nom et l'e-mail, désactive le compte, efface les coordonnées du tuteur, le texte du PV et les
  fichiers de convention. Les numéros de convention, dates, entreprises et notes sont gardés (statistiques).

Les durées et le périmètre sont des HYPOTHÈSES à faire valider par l'école (docs/08, #34).
"""

from django.contrib.auth import get_user_model
from django.db import transaction

from comptes import roles

from .models import Convention, Inscription, annee_universitaire_courante

DOMAINE_ANONYME = "anonyme.invalid"   # « .invalid » : domaine réservé, n'existe jamais
DUREE_CONSERVATION_ANS = 10


def donnees_personnelles(utilisateur):
    """Dictionnaire de tout ce que la plateforme détient sur `utilisateur` (pour répondre à une demande d'accès)."""
    donnees = {
        "compte": {
            "nom": utilisateur.last_name, "prenom": utilisateur.first_name, "email": utilisateur.email,
            "roles": utilisateur.roles(), "actif": utilisateur.is_active,
            "cree_le": utilisateur.date_joined.isoformat(),
            "derniere_connexion": utilisateur.last_login.isoformat() if utilisateur.last_login else None,
        },
        "inscriptions": [str(i.promotion) for i in utilisateur.inscriptions.select_related("promotion")],
        "stages": [],
        "affectations_encadrant": [
            {"annee": a.annee_universitaire, "encadrant": a.encadrant.get_full_name() or a.encadrant.email,
             "active": a.active}
            for a in utilisateur.affectations.select_related("encadrant")
        ],
        "etudiants_encadres": [
            {"annee": a.annee_universitaire, "etudiant": a.etudiant.get_full_name() or a.etudiant.email}
            for a in utilisateur.etudiants_encadres.select_related("etudiant")
        ],
        "soutenances_comme_membre_du_jury": [
            {"etudiant": s.stage.etudiant.get_full_name() or s.stage.etudiant.email,
             "date": s.debut.isoformat() if s.debut else None}
            for s in utilisateur.soutenances_jury.select_related("stage__etudiant")
        ],
    }
    for stage in utilisateur.stages.select_related("entreprise", "promotion"):
        soutenance = getattr(stage, "soutenance", None)
        donnees["stages"].append({
            "promotion": str(stage.promotion), "statut": stage.get_statut_display(),
            "entreprise": stage.entreprise.raison_sociale if stage.entreprise else None,
            "sujet": stage.sujet, "dates": [str(stage.date_debut), str(stage.date_fin)],
            "tuteur": {"nom": stage.tuteur_nom, "email": stage.tuteur_email, "telephone": stage.tuteur_telephone},
            "representant": {"nom": stage.representant_nom, "fonction": stage.representant_fonction},
            "conventions": [{"numero": c.numero, "version": c.version, "statut": c.get_statut_display(),
                             "pdf": bool(c.fichier_pdf), "scan_signe": bool(c.scan_signe)}
                            for c in stage.conventions.all()],
            "livrables": [{"nom": l.nom, "date_limite": str(l.date_limite), "statut": l.get_statut_display()}
                          for l in stage.livrables.all()],
            "soutenance": None if soutenance is None else {
                "date": soutenance.debut.isoformat() if soutenance.debut else None,
                "note": str(soutenance.note) if soutenance.note is not None else None,
                "pv": soutenance.pv,
            },
            "historique": [{"date": h.date.isoformat(), "action": h.get_action_display(), "commentaire": h.commentaire}
                           for h in stage.historique.all()],
        })
    return donnees


def _annee_de_fin(annee_universitaire):
    return int(annee_universitaire[-4:])   # « 2016-2017 » -> 2017


def anciens_comptes(annees=DUREE_CONSERVATION_ANS, annee_courante=None):
    """Comptes d'étudiants dont la dernière inscription est plus vieille que `annees` ans et qui ne sont pas
    déjà anonymisés. Les personnes qui ont un autre rôle (encadrant, jury, Career Center…) sont exclues : on ne
    désactive jamais le compte de quelqu'un qui travaille encore avec la plateforme."""
    debut_courante = int((annee_courante or annee_universitaire_courante())[:4])
    candidats = []
    etudiants = get_user_model().objects.filter(groups__name=roles.ETUDIANT).exclude(
        email__endswith="@" + DOMAINE_ANONYME).distinct()
    for etudiant in etudiants:
        if set(etudiant.roles()) - {roles.ETUDIANT}:
            continue
        dernieres = list(Inscription.objects.filter(etudiant=etudiant).values_list("annee_universitaire", flat=True))
        if dernieres and _annee_de_fin(max(dernieres)) + annees <= debut_courante:
            candidats.append(etudiant)
    return candidats


@transaction.atomic
def anonymiser(etudiant):
    """Anonymise un compte et efface ses données les plus sensibles (voir l'en-tête du module).
    Renvoie le nombre de fichiers supprimés du disque."""
    fichiers = 0
    for stage in etudiant.stages.all():
        stage.tuteur_nom = stage.tuteur_telephone = ""
        stage.tuteur_email = ""
        stage.representant_nom = "(supprimé)"
        stage.save(update_fields=["tuteur_nom", "tuteur_email", "tuteur_telephone", "representant_nom"])
        for convention in stage.conventions.all():
            for champ in (convention.fichier_pdf, convention.scan_signe):
                if champ:
                    champ.delete(save=False)   # supprime le fichier du disque
                    fichiers += 1
            Convention.objects.filter(pk=convention.pk).update(fichier_pdf="", scan_signe="")
        soutenance = getattr(stage, "soutenance", None)
        if soutenance is not None and soutenance.pv:
            soutenance.pv = "(supprimé)"
            soutenance.save(update_fields=["pv"])
    etudiant.first_name = "Ancien"
    etudiant.last_name = f"étudiant n°{etudiant.pk}"
    etudiant.email = f"anonyme-{etudiant.pk}@{DOMAINE_ANONYME}"
    etudiant.is_active = False
    etudiant.is_staff = False
    etudiant.set_unusable_password()
    etudiant.save()
    return fichiers
