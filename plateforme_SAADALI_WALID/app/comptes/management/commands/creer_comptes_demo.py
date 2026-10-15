"""
Commande : python manage.py creer_comptes_demo

Crée (ou réinitialise) des comptes et des données FICTIFS pour tester l'application en local.
- Les e-mails sont en @example.test (domaine réservé aux tests, n'existe pas).
- Les mots de passe sont tirés au hasard et affichés UNE SEULE FOIS dans le
  terminal. Ils ne sont écrits nulle part ailleurs. Relancer la commande en
  génère de nouveaux.
- Données du Lot 1 : promotions de 3e et 5e année (année en cours), Adam en 3e
  (validé par le coordinateur Karim), Yasmine en 5e (encadrée par Sara).
"""

import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from comptes import roles
from soutenances.models import Salle
from stages.models import Inscription, Promotion, annee_universitaire_courante
from stages.services import affecter_encadrant

# (e-mail, prénom, nom, rôles, accès à l'administration ?)
COMPTES_DEMO = [
    ("adam.elamrani@example.test", "Adam", "El Amrani", [roles.ETUDIANT], False),
    ("yasmine.benali@example.test", "Yasmine", "Benali", [roles.ETUDIANT], False),
    ("sara.bennani@example.test", "Sara", "Bennani", [roles.ENCADRANT, roles.JURY], False),
    ("omar.tazi@example.test", "Omar", "Tazi", [roles.ENCADRANT, roles.JURY], False),
    ("karim.idrissi@example.test", "Karim", "Idrissi", [roles.COORDINATEUR], False),
    ("nadia.alaoui@example.test", "Nadia", "Alaoui", [roles.SERVICE_STAGES], True),
]

# Droits du Career Center dans l'administration : comptes, promotions, inscriptions,
# affectations, entreprises et fiches de stage (pas de suppression).
DROITS_SERVICE_STAGES = [
    "view_utilisateur", "add_utilisateur", "change_utilisateur", "view_group",
    "view_promotion", "add_promotion", "change_promotion",
    "view_inscription", "add_inscription", "change_inscription",
    "view_affectation", "add_affectation", "change_affectation",
    "view_entreprise", "add_entreprise", "change_entreprise",
    "view_stage", "change_stage", "view_historique",
    "view_convention", "view_parametresecole", "add_parametresecole", "change_parametresecole",
    "view_livrable", "view_modelelivrable", "add_modelelivrable", "change_modelelivrable", "view_rappel",
    "view_relance",
    "view_salle", "add_salle", "change_salle", "view_campagne", "view_soutenance",
]


class Command(BaseCommand):
    help = "Crée ou réinitialise les comptes et données de démonstration (fictifs)."

    def handle(self, *args, **options):
        Utilisateur = get_user_model()

        # 1. Droits du Career Center dans /admin/
        groupe_ss = Group.objects.get(name=roles.SERVICE_STAGES)
        groupe_ss.permissions.add(*Permission.objects.filter(codename__in=DROITS_SERVICE_STAGES))

        # 2. Création ou mise à jour de chaque compte
        self.stdout.write("Comptes de démonstration (mots de passe affichés une seule fois) :\n")
        comptes = {}
        for email, prenom, nom, liste_roles, acces_admin in COMPTES_DEMO:
            mot_de_passe = secrets.token_urlsafe(9)  # 12 caractères aléatoires
            compte, _cree = Utilisateur.objects.get_or_create(email=email)
            compte.first_name = prenom
            compte.last_name = nom
            compte.is_staff = acces_admin
            compte.set_password(mot_de_passe)
            compte.save()
            compte.groups.set(Group.objects.filter(name__in=liste_roles))
            comptes[prenom] = compte
            self.stdout.write(f"  {email:32} {mot_de_passe:14} {', '.join(liste_roles)}")

        # 3. Promotions, inscriptions et affectation de l'année en cours
        annee = annee_universitaire_courante()
        p3, _ = Promotion.objects.update_or_create(
            annee_etudes=3, annee_universitaire=annee, defaults={"coordinateur": comptes["Karim"]}
        )
        p5, _ = Promotion.objects.get_or_create(annee_etudes=5, annee_universitaire=annee)
        for etudiant, promotion in [(comptes["Adam"], p3), (comptes["Yasmine"], p5)]:
            inscription = Inscription.objects.filter(etudiant=etudiant, annee_universitaire=annee).first()
            if inscription is None:
                Inscription.objects.create(etudiant=etudiant, promotion=promotion)
        affecter_encadrant(comptes["Yasmine"], comptes["Sara"], par=comptes["Nadia"], annee=annee)

        # 4. Salles de soutenance (Lot 6)
        for nom_salle in ("Salle A", "Salle B"):
            Salle.objects.get_or_create(nom=nom_salle)

        self.stdout.write(
            f"\nAnnée {annee} : Adam en 3e (coordinateur Karim), Yasmine en 5e (encadrante Sara)."
        )
        self.stdout.write(self.style.SUCCESS("Terminé. Notez les mots de passe maintenant."))
