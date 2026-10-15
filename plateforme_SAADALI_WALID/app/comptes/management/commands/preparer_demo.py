"""
Commande : python manage.py preparer_demo

Prépare une démonstration complète, avec des données FICTIVES (e-mails en @example.test) :
des étudiants à chaque étape du parcours, pour pouvoir tout montrer en quelques minutes
(voir docs/13-Demo-presentation.md). On utilise les vraies fonctions de l'application (soumettre, valider,
générer la convention, planifier…) : les historiques, e-mails et statuts sont donc ceux d'un vrai dossier.

- Tous les comptes de démonstration ont le MÊME mot de passe (affiché à la fin) : c'est pratique à l'oral,
  et sans danger parce que ces comptes n'existent que dans la base de démonstration.
- Par sécurité, la commande REFUSE de tourner en ligne (DJANGO_DEBUG=0) : un mot de passe connu de tous
  n'a rien à faire sur un vrai site.
- On peut la relancer : ce qui existe déjà n'est pas recréé. Pour repartir de zéro, supprimer le fichier
  de la base de démonstration (demo.sqlite3) puis relancer LANCER_LA_DEMO.bat.
"""

import datetime
import io
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.test.utils import override_settings
from reportlab.pdfgen import canvas

from comptes import roles
from soutenances.models import Campagne, Soutenance
from soutenances.services import (
    enregistrer_disponibilites, generer_soutenances, ouvrir_campagne, proposer_planning, saisir_pv, valider_planning,
)
from stages.models import Entreprise, Historique, Inscription, Promotion, Stage, annee_universitaire_courante
from stages.services import (
    affecter_encadrant, decider_stage, deposer_scan, generer_convention, marquer_envoyee, marquer_rendu,
    soumettre_stage, valider_signature,
)

MOT_DE_PASSE_DEMO = "Demo-EIGSI-2026"

# (e-mail, prénom, nom, année d'études, scénario)
ETUDIANTS = [
    ("adam.elamrani@example.test", "Adam", "El Amrani", 3, "convention_signee"),
    ("imane.bouazza@example.test", "Imane", "Bouazza", 3, "soumis"),
    ("hamza.tahiri@example.test", "Hamza", "Tahiri", 3, "brouillon"),
    ("nour.benjelloun@example.test", "Nour", "Benjelloun", 3, "sans_stage"),
    ("yasmine.benali@example.test", "Yasmine", "Benali", 5, "convention_envoyee"),
    ("salma.cherkaoui@example.test", "Salma", "Cherkaoui", 5, "refuse"),
    ("reda.lamrani@example.test", "Reda", "Lamrani", 5, "valide_sans_convention"),
    ("mehdi.ouazzani@example.test", "Mehdi", "Ouazzani", 5, "pv_saisi"),
    ("kenza.alami@example.test", "Kenza", "Alami", 5, "soutenance_convoquee"),
]

# Entreprises FICTIVES (aucun lien avec une vraie société)
ENTREPRISES = {
    "adam": ("Atlas Digital Services", "Migration de données vers un entrepôt analytique"),
    "imane": ("Sahara Énergie", "Suivi de la production d'un parc solaire par tableau de bord"),
    "hamza": ("Maghreb Logistique", "Optimisation des tournées de livraison"),
    "yasmine": ("Nord Data Systems", "Détection d'anomalies sur des capteurs industriels"),
    "salma": ("Cabinet Ouazzani Ingénierie", "Projet d'amélioration de la qualité"),
    "reda": ("Atlas Digital Services", "Industrialisation d'une chaîne de déploiement continu"),
    "mehdi": ("Sahara Énergie", "Prévision de la consommation électrique par apprentissage automatique"),
    "kenza": ("Maghreb Logistique", "Jumeau numérique d'un entrepôt de distribution"),
}


def verifier(erreurs, contexte):
    """Les fonctions de l'application renvoient une liste de problèmes : on s'arrête si elle n'est pas vide."""
    if erreurs:
        raise CommandError(f"{contexte} : {' '.join(erreurs)}")


def pdf_exemple(titre):
    """Un petit PDF valide (pour la démonstration du dépôt de scan)."""
    tampon = io.BytesIO()
    page = canvas.Canvas(tampon)
    page.setFont("Helvetica", 14)
    page.drawString(72, 760, titre)
    page.setFont("Helvetica", 10)
    page.drawString(72, 740, "Document fictif genere pour la demonstration de la plateforme.")
    page.save()
    return tampon.getvalue()


class Command(BaseCommand):
    help = "Prépare une démonstration complète avec des données fictives (refuse de tourner en ligne)."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Cette commande crée des comptes avec un mot de passe connu de tous : elle ne tourne qu'en "
                "mode développement (DJANGO_DEBUG différent de 0), jamais sur un site en ligne."
            )
        # Les e-mails de l'application ne sont pas affichés pendant la préparation
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            self.preparer()

    def preparer(self):
        Utilisateur = get_user_model()

        # 1. Comptes de base (Career Center, encadrants, coordinateur, deux étudiants), puis mot de passe unique
        call_command("creer_comptes_demo", stdout=StringIO())
        comptes = {u.first_name: u for u in Utilisateur.objects.filter(email__endswith="@example.test")}
        nadia, sara, omar = comptes["Nadia"], comptes["Sara"], comptes["Omar"]
        groupe_etudiant = Group.objects.get(name=roles.ETUDIANT)

        annee = annee_universitaire_courante()
        promotions = {
            3: Promotion.objects.get(annee_etudes=3, annee_universitaire=annee),
            5: Promotion.objects.get(annee_etudes=5, annee_universitaire=annee),
        }

        # 2. Les étudiants et leur inscription
        etudiants = {}
        for email, prenom, nom, annee_etudes, scenario in ETUDIANTS:
            compte, _ = Utilisateur.objects.get_or_create(email=email, defaults={"first_name": prenom, "last_name": nom})
            compte.first_name, compte.last_name = prenom, nom
            compte.save()
            compte.groups.add(groupe_etudiant)
            if not Inscription.objects.filter(etudiant=compte, annee_universitaire=annee).exists():
                Inscription.objects.create(etudiant=compte, promotion=promotions[annee_etudes])
            etudiants[prenom.lower()] = (compte, annee_etudes, scenario)

        # 3. Encadrants des étudiants de 5e année (Yasmine est déjà affectée à Sara)
        for prenom, encadrant in (("yasmine", sara), ("salma", sara), ("mehdi", sara), ("kenza", sara), ("reda", omar)):
            affecter_encadrant(etudiants[prenom][0], encadrant, par=nadia, annee=annee)

        # 4. Un parcours différent par étudiant
        for prenom, (compte, annee_etudes, scenario) in etudiants.items():
            promotion = promotions[annee_etudes]
            if scenario == "sans_stage" or Stage.objects.filter(etudiant=compte, promotion=promotion).exists():
                continue
            self.parcours(prenom, compte, promotion, scenario, nadia)

        # 5. Soutenances de septembre 2027 (étudiants de 5e dont la convention est signée)
        self.soutenances(annee, nadia, sara, omar)

        # 6. Mot de passe unique et récapitulatif
        for compte in Utilisateur.objects.filter(email__endswith="@example.test"):
            compte.set_password(MOT_DE_PASSE_DEMO)
            compte.save(update_fields=["password"])
        self.recapitulatif(annee)

    # ------------------------------------------------------------------ parcours

    def parcours(self, prenom, etudiant, promotion, scenario, nadia):
        nom_entreprise, sujet = ENTREPRISES[prenom]
        entreprise, _ = Entreprise.objects.get_or_create(
            raison_sociale=nom_entreprise, defaults={"ville": "Casablanca", "email_contact": "contact@example.test"})
        cinquieme = promotion.annee_etudes == 5
        debut, fin = (datetime.date(2027, 2, 1), datetime.date(2027, 7, 31)) if cinquieme else \
                     (datetime.date(2027, 6, 14), datetime.date(2027, 7, 30))
        champs = dict(
            etudiant=etudiant, promotion=promotion, entreprise=entreprise, origine="RESEAU", sujet=sujet,
            representant_nom="M. Alaoui", representant_fonction="Directeur des ressources humaines",
            tuteur_nom="Mme Tazi", tuteur_email=f"tuteur.{prenom}@example.test", tuteur_telephone="0522000000",
            date_debut=debut, date_fin=fin, heures_max_semaine=40,
        )
        if scenario == "brouillon":   # fiche volontairement incomplète
            champs.update(representant_nom="", representant_fonction="", tuteur_nom="", tuteur_email="", date_fin=None)
        stage = Stage.objects.create(**champs)
        Historique.objects.create(stage=stage, auteur=etudiant, action=Historique.Action.CREATION)
        if scenario == "brouillon":
            return

        verifier(soumettre_stage(stage, par=etudiant), f"Soumission ({prenom})")
        valideur = stage.valideur()
        if scenario == "soumis":
            return
        if scenario == "refuse":
            verifier(decider_stage(stage, valideur, valider=False,
                                   motif="Le sujet est trop général : précisez les activités confiées et les outils utilisés."),
                     f"Refus ({prenom})")
            return
        verifier(decider_stage(stage, valideur, valider=True, motif=""), f"Validation ({prenom})")
        if scenario == "valide_sans_convention":
            return

        convention, erreurs = generer_convention(stage, nadia)
        verifier(erreurs, f"Convention ({prenom})")
        verifier(marquer_envoyee(convention, nadia), f"Envoi de la convention ({prenom})")
        if scenario == "convention_envoyee":
            return

        scan = SimpleUploadedFile(f"scan-{prenom}.pdf", pdf_exemple(f"Convention signee de {prenom.title()}"),
                                  content_type="application/pdf")
        verifier(deposer_scan(convention, scan, etudiant), f"Dépôt du scan ({prenom})")
        verifier(valider_signature(convention, nadia), f"Signature ({prenom})")
        livrables = list(stage.livrables.order_by("date_limite"))
        if scenario == "convention_signee":    # un livrable rendu, les autres à rendre
            for livrable in livrables[:1]:
                marquer_rendu(livrable, nadia)
        else:                                    # soutenance : tout est rendu
            for livrable in livrables:
                marquer_rendu(livrable, nadia)

    # --------------------------------------------------------------- soutenances

    def soutenances(self, annee, nadia, sara, omar):
        if Campagne.objects.filter(annee_universitaire=annee, nom__startswith="Soutenances PFE").exists():
            return
        campagne = Campagne.objects.create(
            nom="Soutenances PFE, septembre 2027", annee_universitaire=annee, annees_concernees="5",
            date_debut=datetime.date(2027, 9, 6), date_fin=datetime.date(2027, 9, 10))
        ouvrir_campagne(campagne)
        generer_soutenances(campagne)
        creneaux = campagne.creneaux()[:20]
        for jure in (sara, omar):
            verifier(enregistrer_disponibilites(campagne, jure, creneaux), "Disponibilités du jury")
        resultat = proposer_planning(campagne)
        verifier(resultat["erreurs"], "Planning des soutenances")
        verifier(valider_planning(campagne, nadia), "Validation du planning")

        # Mehdi : PV déjà saisi par le jury (le Career Center le valide pendant la démonstration)
        soutenance = Soutenance.objects.get(stage__etudiant__email="mehdi.ouazzani@example.test")
        membre = soutenance.jury.first()
        verifier(saisir_pv(soutenance, membre, "15,5",
                           "Présentation claire, bonne maîtrise technique. Résultats convaincants ; "
                           "la partie évaluation des risques pourrait être approfondie."), "PV de Mehdi")

    # ------------------------------------------------------------- récapitulatif

    def recapitulatif(self, annee):
        self.stdout.write(self.style.SUCCESS(f"\nDémonstration prête (année {annee})."))
        self.stdout.write(f"Mot de passe de TOUS les comptes : {MOT_DE_PASSE_DEMO}\n")
        lignes = [
            ("nadia.alaoui", "Service Stages (Career Center)", "pilote tout : tableau de bord, conventions, soutenances"),
            ("adam.elamrani", "Étudiant 3e", "convention signée, 1 livrable rendu"),
            ("imane.bouazza", "Étudiante 3e", "fiche soumise : le coordinateur la valide"),
            ("hamza.tahiri", "Étudiant 3e", "fiche en brouillon, incomplète"),
            ("nour.benjelloun", "Étudiante 3e", "n'a pas encore déclaré de stage"),
            ("yasmine.benali", "Étudiante 5e", "convention envoyée : elle dépose son scan"),
            ("salma.cherkaoui", "Étudiante 5e", "fiche refusée avec motif"),
            ("reda.lamrani", "Étudiant 5e", "stage validé : le Career Center génère la convention"),
            ("mehdi.ouazzani", "Étudiant 5e", "soutenance passée : PV à valider"),
            ("kenza.alami", "Étudiante 5e", "soutenance planifiée : le jury saisit le PV"),
            ("karim.idrissi", "Coordinateur 3e", "valide les fiches de la 3e année"),
            ("sara.bennani", "Encadrante et jury", "valide les fiches de la 5e, saisit les PV"),
            ("omar.tazi", "Encadrant et jury", ""),
        ]
        for adresse, role, role_demo in lignes:
            self.stdout.write(f"  {adresse + '@example.test':34} {role:32} {role_demo}")
