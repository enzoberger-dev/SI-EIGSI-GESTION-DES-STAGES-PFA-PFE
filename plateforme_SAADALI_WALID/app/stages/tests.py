"""
Tests automatiques du suivi des stages. Lancer : python manage.py test
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase

from comptes import roles

from .models import (
    Affectation, Entreprise, Historique, Inscription, Promotion, Stage, annee_universitaire_courante,
)
from .services import affecter_encadrant, decider_stage, soumettre_stage


def creer(email, *liste_roles, prenom="Test", nom="Utilisateur"):
    """Crée un utilisateur de test avec les rôles donnés."""
    u = get_user_model().objects.create_user(email, "MotDePasse-123", first_name=prenom, last_name=nom)
    u.groups.set(Group.objects.filter(name__in=liste_roles))
    return u


class BaseStages(TestCase):
    """Données communes : une promotion de 3e et une de 5e, des étudiants et des encadrants."""

    def setUp(self):
        self.annee = annee_universitaire_courante()
        self.career = creer("career@example.test", roles.SERVICE_STAGES, prenom="Nadia")
        self.coordinateur = creer("coord@example.test", roles.COORDINATEUR, prenom="Karim")
        self.encadrant = creer("sara@example.test", roles.ENCADRANT, prenom="Sara")
        self.encadrant2 = creer("omar@example.test", roles.ENCADRANT, prenom="Omar")
        self.p3 = Promotion.objects.create(annee_etudes=3, annee_universitaire=self.annee, coordinateur=self.coordinateur)
        self.p5 = Promotion.objects.create(annee_etudes=5, annee_universitaire=self.annee)
        self.etu3 = creer("adam@example.test", roles.ETUDIANT, prenom="Adam")
        self.etu5 = creer("yasmine@example.test", roles.ETUDIANT, prenom="Yasmine")
        Inscription.objects.create(etudiant=self.etu3, promotion=self.p3)
        Inscription.objects.create(etudiant=self.etu5, promotion=self.p5)


class AffectationEcranTests(BaseStages):
    def test_page_reservee_au_career_center(self):
        self.client.force_login(self.etu5)
        self.assertEqual(self.client.get("/service-stages/affectations/").status_code, 403)
        self.client.force_login(self.career)
        self.assertEqual(self.client.get("/service-stages/affectations/").status_code, 200)

    def test_seuls_les_etudiants_de_4e_et_5e_sont_listes(self):
        self.client.force_login(self.career)
        page = self.client.get("/service-stages/affectations/").content.decode()
        self.assertIn("Yasmine", page)
        self.assertNotIn("Adam", page)

    def test_affecter_depuis_l_ecran(self):
        self.client.force_login(self.career)
        self.client.post("/service-stages/affectations/", {"etudiant": self.etu5.id, "encadrant": self.encadrant.id})
        a = Affectation.objects.get(etudiant=self.etu5, active=True)
        self.assertEqual(a.encadrant, self.encadrant)
        self.assertEqual(a.affecte_par, self.career)

    def test_refuse_une_personne_qui_n_est_pas_encadrant(self):
        self.client.force_login(self.career)
        self.client.post("/service-stages/affectations/", {"etudiant": self.etu5.id, "encadrant": self.etu3.id})
        self.assertFalse(Affectation.objects.exists())

    def test_refuse_un_etudiant_de_3e_annee(self):
        self.client.force_login(self.career)
        self.client.post("/service-stages/affectations/", {"etudiant": self.etu3.id, "encadrant": self.encadrant.id})
        self.assertFalse(Affectation.objects.exists())


class AffecterEncadrantTests(BaseStages):
    def test_previent_encadrant_et_etudiant_par_email(self):
        affecter_encadrant(self.etu5, self.encadrant, par=self.career, annee=self.annee)
        destinataires = [m.to[0] for m in mail.outbox]
        self.assertEqual(sorted(destinataires), ["sara@example.test", "yasmine@example.test"])

    def test_changer_d_encadrant_garde_l_historique(self):
        affecter_encadrant(self.etu5, self.encadrant, par=self.career, annee=self.annee)
        affecter_encadrant(self.etu5, self.encadrant2, par=self.career, annee=self.annee)
        self.assertEqual(Affectation.objects.filter(etudiant=self.etu5).count(), 2)
        active = Affectation.objects.get(etudiant=self.etu5, active=True)
        self.assertEqual(active.encadrant, self.encadrant2)

    def test_reaffecter_le_meme_encadrant_ne_change_rien(self):
        affecter_encadrant(self.etu5, self.encadrant, par=self.career, annee=self.annee)
        affecter_encadrant(self.etu5, self.encadrant, par=self.career, annee=self.annee)
        self.assertEqual(Affectation.objects.filter(etudiant=self.etu5).count(), 1)

    def test_inscrit_dans_l_historique_du_stage_existant(self):
        stage = Stage.objects.create(etudiant=self.etu5, promotion=self.p5)
        affecter_encadrant(self.etu5, self.encadrant, par=self.career, annee=self.annee)
        self.assertTrue(stage.historique.filter(action=Historique.Action.AFFECTATION).exists())


class ReglesStageTests(BaseStages):
    def test_valideur_5e_annee_est_l_encadrant(self):
        stage = Stage.objects.create(etudiant=self.etu5, promotion=self.p5)
        self.assertIsNone(stage.valideur())
        affecter_encadrant(self.etu5, self.encadrant, par=self.career, annee=self.annee)
        self.assertEqual(stage.valideur(), self.encadrant)

    def test_valideur_3e_annee_est_le_coordinateur(self):
        stage = Stage.objects.create(etudiant=self.etu3, promotion=self.p3)
        self.assertEqual(stage.valideur(), self.coordinateur)

    def test_type_de_stage_deduit_de_l_annee(self):
        self.assertEqual(Stage(etudiant=self.etu3, promotion=self.p3).type_stage, "Technicien")
        self.assertEqual(Stage(etudiant=self.etu5, promotion=self.p5).type_stage, "Fin d'Études")

    def test_duree_minimale_selon_le_type(self):
        debut = date(2027, 2, 1)
        trop_court = Stage(etudiant=self.etu3, promotion=self.p3, date_debut=debut, date_fin=debut + timedelta(weeks=4))
        self.assertTrue(any("au moins 6 semaines" in e for e in trop_court.erreurs_soumission()))
        assez_long = Stage(etudiant=self.etu3, promotion=self.p3, date_debut=debut, date_fin=debut + timedelta(weeks=8))
        self.assertFalse(any("au moins" in e for e in assez_long.erreurs_soumission()))

    def test_soumission_impossible_sans_encadrant_en_5e(self):
        stage = Stage(etudiant=self.etu5, promotion=self.p5)
        self.assertTrue(any("Aucun encadrant" in e for e in stage.erreurs_soumission()))

    def test_brouillon_vide_signale_les_champs_manquants(self):
        stage = Stage(etudiant=self.etu3, promotion=self.p3)
        self.assertTrue(any("Champs obligatoires" in e for e in stage.erreurs_soumission()))


def fiche_complete(**changements):
    """Données d'une fiche complète (stage Technicien de 8 semaines), modifiables."""
    donnees = {
        "entreprise_nom": "Atlas Énergies", "entreprise_ville": "Casablanca", "entreprise_pays": "Maroc",
        "origine": "RESEAU", "sujet": "Maintenance du parc informatique",
        "representant_nom": "M. Exemple", "representant_fonction": "Gérant",
        "tuteur_nom": "Mme Tutrice", "tuteur_email": "tutrice@example.test",
        "date_debut": "2027-06-01", "date_fin": "2027-07-27", "heures_max_semaine": "35",
    }
    donnees.update(changements)
    return donnees


class EcransEtudiantTests(BaseStages):
    URL_FICHE = "/etudiant/mon-stage/modifier/"

    def test_pages_reservees_aux_etudiants(self):
        self.client.force_login(self.encadrant)
        self.assertEqual(self.client.get("/etudiant/mon-stage/").status_code, 403)
        self.client.force_login(self.etu3)
        self.assertEqual(self.client.get("/etudiant/mon-stage/").status_code, 200)
        self.assertEqual(self.client.get(self.URL_FICHE).status_code, 200)

    def test_etudiant_non_inscrit_est_prevenu(self):
        sans_promo = creer("seul@example.test", roles.ETUDIANT)
        self.client.force_login(sans_promo)
        page = self.client.get("/etudiant/mon-stage/").content.decode()
        self.assertIn("aucune promotion", page)

    def test_brouillon_incomplet_enregistre_sans_email(self):
        self.client.force_login(self.etu3)
        self.client.post(self.URL_FICHE, {"sujet": "Idée de sujet", "brouillon": ""})
        stage = Stage.objects.get(etudiant=self.etu3)
        self.assertEqual(stage.statut, Stage.Statut.BROUILLON)
        self.assertTrue(stage.historique.filter(action=Historique.Action.CREATION).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_soumission_incomplete_refusee(self):
        self.client.force_login(self.etu3)
        self.client.post(self.URL_FICHE, {"sujet": "Idée de sujet", "soumettre": ""})
        self.assertEqual(Stage.objects.get(etudiant=self.etu3).statut, Stage.Statut.BROUILLON)
        self.assertEqual(len(mail.outbox), 0)

    def test_soumission_complete_previent_le_coordinateur(self):
        self.client.force_login(self.etu3)
        self.client.post(self.URL_FICHE, fiche_complete(soumettre=""))
        stage = Stage.objects.get(etudiant=self.etu3)
        self.assertEqual(stage.statut, Stage.Statut.SOUMIS)
        self.assertTrue(stage.historique.filter(action=Historique.Action.SOUMISSION).exists())
        self.assertEqual(mail.outbox[-1].to, ["coord@example.test"])

    def test_entreprise_existante_reutilisee(self):
        Entreprise.objects.create(raison_sociale="Atlas Énergies", ville="Rabat")
        self.client.force_login(self.etu3)
        self.client.post(self.URL_FICHE, fiche_complete(entreprise_nom="atlas énergies", brouillon=""))
        self.assertEqual(Entreprise.objects.count(), 1)
        self.assertEqual(Stage.objects.get(etudiant=self.etu3).entreprise.ville, "Rabat")

    def test_fiche_soumise_non_modifiable(self):
        self.client.force_login(self.etu3)
        self.client.post(self.URL_FICHE, fiche_complete(soumettre=""))
        self.client.post(self.URL_FICHE, fiche_complete(sujet="Sujet changé", brouillon=""))
        stage = Stage.objects.get(etudiant=self.etu3)
        self.assertEqual(stage.sujet, "Maintenance du parc informatique")
        self.assertEqual(stage.statut, Stage.Statut.SOUMIS)

    def test_date_de_fin_avant_debut_refusee(self):
        self.client.force_login(self.etu3)
        reponse = self.client.post(self.URL_FICHE, fiche_complete(date_fin="2027-05-01", brouillon=""))
        self.assertContains(reponse, "La date de fin doit être après la date de début.")
        self.assertFalse(Stage.objects.exists())

    def test_5e_annee_sans_encadrant_ne_peut_pas_soumettre(self):
        self.client.force_login(self.etu5)
        self.client.post(self.URL_FICHE, fiche_complete(
            date_debut="2027-02-01", date_fin="2027-07-31", soumettre=""))
        self.assertEqual(Stage.objects.get(etudiant=self.etu5).statut, Stage.Statut.BROUILLON)


class ValidationTests(BaseStages):
    """US-02 : validation ou refus par le valideur (encadrant en 5e, coordinateur en 3e)."""

    def stage_soumis(self, etudiant, promotion, semaines):
        entreprise, _ = Entreprise.objects.get_or_create(raison_sociale="Atlas Énergies")
        stage = Stage.objects.create(
            etudiant=etudiant, promotion=promotion, entreprise=entreprise, origine="RESEAU",
            sujet="Sujet de test", representant_nom="M. Exemple", representant_fonction="Gérant",
            tuteur_nom="Mme Tutrice", tuteur_email="tutrice@example.test",
            date_debut=date(2027, 2, 1), date_fin=date(2027, 2, 1) + timedelta(weeks=semaines),
            heures_max_semaine=35,
        )
        self.assertEqual(soumettre_stage(stage, par=etudiant), [])
        mail.outbox.clear()
        return stage

    def setUp(self):
        super().setUp()
        affecter_encadrant(self.etu5, self.encadrant, par=self.career, annee=self.annee)
        self.stage3 = self.stage_soumis(self.etu3, self.p3, 8)
        self.stage5 = self.stage_soumis(self.etu5, self.p5, 26)

    def test_chacun_ne_voit_que_ses_fiches(self):
        self.client.force_login(self.coordinateur)
        page = self.client.get("/validation/").content.decode()
        self.assertIn("Adam", page)
        self.assertNotIn("Yasmine", page)
        self.client.force_login(self.encadrant)
        page = self.client.get("/validation/").content.decode()
        self.assertIn("Yasmine", page)
        self.assertNotIn("Adam", page)

    def test_un_autre_encadrant_ne_peut_pas_ouvrir_la_fiche(self):
        self.client.force_login(self.encadrant2)
        self.assertEqual(self.client.get(f"/validation/{self.stage5.pk}/").status_code, 403)

    def test_un_etudiant_n_a_pas_acces(self):
        self.client.force_login(self.etu5)
        self.assertEqual(self.client.get("/validation/").status_code, 403)

    def test_valider_previent_l_etudiant(self):
        self.client.force_login(self.encadrant)
        self.client.post(f"/validation/{self.stage5.pk}/", {"decision": "valider", "motif": ""})
        self.stage5.refresh_from_db()
        self.assertEqual(self.stage5.statut, Stage.Statut.VALIDE)
        self.assertTrue(self.stage5.historique.filter(action=Historique.Action.VALIDATION, auteur=self.encadrant).exists())
        self.assertEqual(mail.outbox[-1].to, ["yasmine@example.test"])

    def test_refus_sans_motif_impossible(self):
        self.client.force_login(self.coordinateur)
        reponse = self.client.post(f"/validation/{self.stage3.pk}/", {"decision": "refuser", "motif": "  "})
        self.assertContains(reponse, "Un refus doit être accompagné d&#x27;un motif.")
        self.stage3.refresh_from_db()
        self.assertEqual(self.stage3.statut, Stage.Statut.SOUMIS)

    def test_refus_puis_correction_et_nouvelle_soumission(self):
        self.client.force_login(self.coordinateur)
        self.client.post(f"/validation/{self.stage3.pk}/", {"decision": "refuser", "motif": "Sujet trop vague"})
        self.stage3.refresh_from_db()
        self.assertEqual(self.stage3.statut, Stage.Statut.REFUSE)
        self.assertIn("Sujet trop vague", mail.outbox[-1].body)
        # L'étudiant voit le motif, corrige et soumet de nouveau
        self.client.force_login(self.etu3)
        self.assertContains(self.client.get("/etudiant/mon-stage/"), "Sujet trop vague")
        self.client.post("/etudiant/mon-stage/modifier/", fiche_complete(sujet="Sujet précisé", soumettre=""))
        self.stage3.refresh_from_db()
        self.assertEqual(self.stage3.statut, Stage.Statut.SOUMIS)
        self.assertEqual(self.stage3.sujet, "Sujet précisé")

    def test_pas_de_seconde_decision(self):
        self.assertEqual(decider_stage(self.stage5, par=self.encadrant, valider=True), [])
        erreurs = decider_stage(self.stage5, par=self.encadrant, valider=False, motif="Changement d'avis")
        self.assertEqual(erreurs, ["Cette fiche n'est pas en attente de décision."])

    def test_seul_le_valideur_peut_decider(self):
        erreurs = decider_stage(self.stage5, par=self.coordinateur, valider=True)
        self.assertEqual(erreurs, ["Vous n'êtes pas le valideur de ce stage."])

    def test_espace_coordinateur(self):
        self.client.force_login(self.coordinateur)
        self.assertEqual(self.client.get("/coordinateur/").status_code, 200)
        self.assertContains(self.client.get("/"), "Espace coordinateur de promotion")


# ---------------------------------------------------------------------------
# Lot 2 : convention
# ---------------------------------------------------------------------------
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from .models import Convention
from .services import (
    convention_en_vigueur, deposer_scan, generer_convention, marquer_envoyee, refuser_scan, valider_signature,
)

DOSSIER_TEST = tempfile.mkdtemp(prefix="stages-tests-")
PDF_FACTICE = b"%PDF-1.4\n%contenu de test\n"


@override_settings(MEDIA_ROOT=DOSSIER_TEST)
class ConventionTests(BaseStages):
    """Lot 2 : génération du PDF, envoi, dépôt du scan, signature, sécurité des fichiers."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(DOSSIER_TEST, ignore_errors=True)

    def stage_valide(self, etudiant=None, promotion=None, **champs):
        etudiant, promotion = etudiant or self.etu3, promotion or self.p3
        entreprise, _ = Entreprise.objects.get_or_create(
            raison_sociale="Atlas <Énergies> & Cie", defaults={"ville": "Casablanca"})
        donnees = dict(
            etudiant=etudiant, promotion=promotion, entreprise=entreprise, origine="RESEAU",
            sujet="Sujet de test", representant_nom="M. Exemple", representant_fonction="Gérant",
            tuteur_nom="Mme Tutrice", tuteur_email="tutrice@example.test",
            date_debut=date(2027, 2, 1), date_fin=date(2027, 4, 1), heures_max_semaine=35,
            statut=Stage.Statut.VALIDE,
        )
        donnees.update(champs)
        return Stage.objects.create(**donnees)

    def scan(self, nom="scan.pdf", contenu=PDF_FACTICE):
        return SimpleUploadedFile(nom, contenu)

    def convention_envoyee(self):
        stage = self.stage_valide()
        convention, _ = generer_convention(stage, par=self.career)
        marquer_envoyee(convention, par=self.career)
        convention.refresh_from_db()
        return convention

    # --- génération ------------------------------------------------------
    def test_generation_cree_un_pdf_numerote(self):
        stage = self.stage_valide()
        convention, erreurs = generer_convention(stage, par=self.career)
        self.assertEqual(erreurs, [])
        self.assertRegex(convention.numero, r"^\d{4}-0001$")
        self.assertEqual(convention.version, 1)
        contenu = convention.fichier_pdf.read()
        self.assertTrue(contenu.startswith(b"%PDF"))
        self.assertGreater(len(contenu), 3000)
        self.assertTrue(stage.historique.filter(action=Historique.Action.CONVENTION_GENEREE).exists())

    def test_numeros_se_suivent(self):
        premiere, _ = generer_convention(self.stage_valide(), par=self.career)
        seconde, _ = generer_convention(self.stage_valide(self.etu5, self.p5), par=self.career)
        self.assertEqual(int(seconde.numero[-4:]), int(premiere.numero[-4:]) + 1)

    def test_stage_non_valide_refuse(self):
        stage = self.stage_valide(statut=Stage.Statut.SOUMIS)
        convention, erreurs = generer_convention(stage, par=self.career)
        self.assertIsNone(convention)
        self.assertTrue(erreurs)

    def test_regenerer_cree_une_nouvelle_version_et_garde_l_ancienne(self):
        stage = self.stage_valide()
        v1, _ = generer_convention(stage, par=self.career)
        v2, _ = generer_convention(stage, par=self.career)
        v1.refresh_from_db()
        self.assertEqual((v2.numero, v2.version), (v1.numero, 2))
        self.assertEqual(v1.statut, Convention.Statut.REMPLACEE)
        self.assertEqual(convention_en_vigueur(stage), v2)
        self.assertEqual(stage.conventions.count(), 2)

    def test_caracteres_speciaux_ne_cassent_pas_le_pdf(self):
        stage = self.stage_valide(sujet="Sujet avec <b>balises</b> & \"guillemets\" é à ç")
        convention, erreurs = generer_convention(stage, par=self.career)
        self.assertEqual(erreurs, [])
        self.assertTrue(convention.fichier_pdf.read().startswith(b"%PDF"))

    # --- circuit de signature --------------------------------------------
    def test_envoi_previent_l_etudiant_avec_le_pdf_en_piece_jointe(self):
        stage = self.stage_valide()
        convention, _ = generer_convention(stage, par=self.career)
        self.assertEqual(marquer_envoyee(convention, par=self.career), [])
        convention.refresh_from_db()
        self.assertEqual(convention.statut, Convention.Statut.ENVOYEE)
        message = mail.outbox[-1]
        self.assertEqual(message.to, ["adam@example.test"])
        self.assertEqual(len(message.attachments), 1)

    def test_circuit_complet(self):
        convention = self.convention_envoyee()
        self.assertEqual(deposer_scan(convention, self.scan(), par=self.etu3), [])
        convention.refresh_from_db()
        self.assertTrue(convention.scan_signe)
        self.assertEqual(valider_signature(convention, par=self.career), [])
        convention.refresh_from_db()
        self.assertEqual(convention.statut, Convention.Statut.SIGNEE)
        self.assertIsNotNone(convention.signee_le)

    def test_convention_signee_est_verrouillee(self):
        convention = self.convention_envoyee()
        deposer_scan(convention, self.scan(), par=self.etu3)
        valider_signature(convention, par=self.career)
        _, erreurs = generer_convention(convention.stage, par=self.career)
        self.assertEqual(erreurs, ["La convention est déjà signée : elle est verrouillée."])

    def test_scan_impossible_avant_l_envoi(self):
        convention, _ = generer_convention(self.stage_valide(), par=self.career)
        self.assertTrue(deposer_scan(convention, self.scan(), par=self.etu3))

    def test_signature_impossible_sans_scan(self):
        convention = self.convention_envoyee()
        self.assertTrue(valider_signature(convention, par=self.career))

    def test_scan_refuse_puis_redepose(self):
        convention = self.convention_envoyee()
        deposer_scan(convention, self.scan(), par=self.etu3)
        convention.refresh_from_db()
        self.assertEqual(refuser_scan(convention, par=self.career, motif=""), ["Un refus doit être accompagné d'un motif."])
        self.assertEqual(refuser_scan(convention, par=self.career, motif="Page 3 manquante"), [])
        convention.refresh_from_db()
        self.assertFalse(convention.scan_signe)
        self.assertIn("Page 3 manquante", mail.outbox[-1].body)
        self.assertEqual(deposer_scan(convention, self.scan(), par=self.etu3), [])

    # --- contrôle des fichiers déposés -----------------------------------
    def test_scan_format_refuse(self):
        convention = self.convention_envoyee()
        self.assertTrue(deposer_scan(convention, self.scan("virus.exe", b"MZ..."), par=self.etu3))

    def test_scan_faux_pdf_refuse(self):
        convention = self.convention_envoyee()
        erreurs = deposer_scan(convention, self.scan("scan.pdf", b"<html>pas un pdf</html>"), par=self.etu3)
        self.assertEqual(erreurs, ["Le contenu du fichier ne correspond pas à son format."])

    def test_scan_trop_gros_refuse(self):
        convention = self.convention_envoyee()
        with override_settings(TAILLE_MAX_SCAN=10):
            erreurs = deposer_scan(convention, self.scan(), par=self.etu3)
        self.assertTrue(erreurs and "trop gros" in erreurs[0])

    # --- sécurité des écrans et téléchargements --------------------------
    def test_pages_career_center_interdites_aux_autres(self):
        for compte in (self.etu3, self.encadrant, self.coordinateur):
            self.client.force_login(compte)
            self.assertEqual(self.client.get("/service-stages/conventions/").status_code, 403)
        self.client.force_login(self.career)
        self.assertEqual(self.client.get("/service-stages/conventions/").status_code, 200)

    def test_actions_career_center_refusees_en_get_et_aux_etudiants(self):
        stage = self.stage_valide()
        self.client.force_login(self.career)
        self.assertEqual(self.client.get(f"/service-stages/conventions/generer/{stage.pk}/").status_code, 405)
        self.client.force_login(self.etu3)
        self.assertEqual(self.client.post(f"/service-stages/conventions/generer/{stage.pk}/").status_code, 403)
        self.assertFalse(Convention.objects.exists())

    def test_telechargement_reserve_au_proprietaire_et_au_career_center(self):
        convention = self.convention_envoyee()
        url = f"/convention/{convention.pk}/pdf/"
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)  # renvoyé vers la connexion
        self.client.force_login(self.etu5)  # un autre étudiant
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.encadrant)
        self.assertEqual(self.client.get(url).status_code, 403)
        for autorise in (self.etu3, self.career):
            self.client.force_login(autorise)
            reponse = self.client.get(url)
            self.assertEqual(reponse.status_code, 200)
            self.assertEqual(reponse["Content-Type"], "application/pdf")
            self.assertTrue(b"".join(reponse.streaming_content).startswith(b"%PDF"))

    def test_telechargement_d_un_fichier_inexistant_ou_inconnu(self):
        convention = self.convention_envoyee()
        self.client.force_login(self.career)
        self.assertEqual(self.client.get(f"/convention/{convention.pk}/scan/").status_code, 404)  # pas de scan
        self.assertEqual(self.client.get(f"/convention/{convention.pk}/../../etc/").status_code, 404)
        self.assertEqual(self.client.get(f"/convention/{convention.pk}/autre/").status_code, 404)

    def test_parcours_par_les_ecrans(self):
        stage = self.stage_valide()
        # Career Center : génère puis envoie
        self.client.force_login(self.career)
        self.client.post(f"/service-stages/conventions/generer/{stage.pk}/")
        convention = convention_en_vigueur(stage)
        self.client.post(f"/service-stages/conventions/{convention.pk}/envoyer/")
        # Étudiant : voit sa convention et dépose le scan
        self.client.force_login(self.etu3)
        self.assertContains(self.client.get("/etudiant/mon-stage/"), f"Ma convention n° {convention.numero}")
        self.client.post("/etudiant/convention/scan/", {"scan": self.scan()})
        convention.refresh_from_db()
        self.assertTrue(convention.scan_signe)
        # Career Center : valide
        self.client.force_login(self.career)
        self.client.post(f"/service-stages/conventions/{convention.pk}/valider/")
        convention.refresh_from_db()
        self.assertEqual(convention.statut, Convention.Statut.SIGNEE)
        self.client.force_login(self.etu3)
        self.assertContains(self.client.get("/etudiant/mon-stage/"), "Signée par toutes les parties")


# ---------------------------------------------------------------------------
# Lot 3 bis : livrables rendus sur Moodle et rappels automatiques
# ---------------------------------------------------------------------------
from io import StringIO
from unittest import mock

from django.core.management import CommandError, call_command

from .models import Livrable, ModeleLivrable, ParametresEcole, Rappel
from .services import (
    annuler_rendu, creer_livrables, envoyer_rappels, marquer_rendu, prolonger_livrable,
)


class LivrableBase(BaseStages):
    def entreprise(self):
        return Entreprise.objects.get_or_create(raison_sociale="Atlas Énergies")[0]

    def stage_valide(self, etudiant, promotion, debut, fin, **champs):
        return Stage.objects.create(
            etudiant=etudiant, promotion=promotion, entreprise=self.entreprise(), origine="RESEAU", sujet="S",
            representant_nom="M. Exemple", representant_fonction="Gérant", tuteur_nom="Mme Tutrice",
            tuteur_email="tutrice@example.test", date_debut=debut, date_fin=fin, heures_max_semaine=35,
            statut=Stage.Statut.VALIDE, **champs,
        )


class CreationLivrablesTests(LivrableBase):
    def test_technicien_seulement_le_rapport_au_15_septembre(self):
        stage = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        creer_livrables(stage)
        self.assertEqual(list(stage.livrables.values_list("nom", "date_limite")),
                         [("Rapport de stage", date(2027, 9, 15))])
        stage.refresh_from_db()
        self.assertEqual(stage.date_limite_rapport, date(2027, 9, 15))

    def test_fin_d_etudes_plan_directeur_rapport_et_evaluation_des_competences(self):
        stage = self.stage_valide(self.etu5, self.p5, date(2027, 2, 1), date(2027, 7, 31))
        creer_livrables(stage)
        dates = {l.nom: l.date_limite for l in stage.livrables.all()}
        self.assertEqual(dates, {
            "Plan directeur": date(2027, 3, 1),                              # début + 4 semaines
            "Rapport de stage": date(2027, 9, 15),
            "Évaluation des compétences (tuteur entreprise)": date(2027, 9, 15),
        })

    def test_date_fixe_avant_la_fin_du_stage_donne_14_jours_apres_la_fin(self):
        stage = self.stage_valide(self.etu3, self.p3, date(2027, 8, 1), date(2027, 10, 1))
        creer_livrables(stage)
        self.assertEqual(stage.livrables.get().date_limite, date(2027, 10, 15))

    def test_creation_repetee_sans_doublon(self):
        stage = self.stage_valide(self.etu5, self.p5, date(2027, 2, 1), date(2027, 7, 31))
        creer_livrables(stage)
        self.assertEqual(creer_livrables(stage), [])
        self.assertEqual(stage.livrables.count(), 3)

    def test_la_signature_de_la_convention_cree_les_livrables(self):
        stage = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        convention, _ = generer_convention(stage, par=self.career)
        marquer_envoyee(convention, par=self.career)
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            deposer_scan(convention, SimpleUploadedFile("s.pdf", PDF_FACTICE), par=self.etu3)
        valider_signature(convention, par=self.career)
        self.assertEqual(stage.livrables.count(), 1)


class SuiviLivrablesTests(LivrableBase):
    def setUp(self):
        super().setUp()
        self.stage = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        creer_livrables(self.stage)
        self.livrable = self.stage.livrables.get()
        mail.outbox.clear()

    def test_marquer_rendu_puis_annuler(self):
        self.assertEqual(marquer_rendu(self.livrable, par=self.career), [])
        self.livrable.refresh_from_db()
        self.assertEqual((self.livrable.statut, self.livrable.rendu_par), (Livrable.Statut.RENDU, self.career))
        self.assertTrue(self.stage.historique.filter(action=Historique.Action.LIVRABLE_RENDU).exists())
        self.assertTrue(marquer_rendu(self.livrable, par=self.career))      # déjà rendu
        self.assertEqual(annuler_rendu(self.livrable, par=self.career), [])
        self.livrable.refresh_from_db()
        self.assertEqual(self.livrable.statut, Livrable.Statut.A_RENDRE)

    def test_seul_le_career_center_marque_rendu(self):
        url = f"/service-stages/suivi/{self.livrable.pk}/rendu/"
        for compte in (self.etu3, self.coordinateur, self.encadrant):
            self.client.force_login(compte)
            self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.career)
        self.assertEqual(self.client.get(url).status_code, 405)              # pas en GET
        self.client.post(url)
        self.livrable.refresh_from_db()
        self.assertEqual(self.livrable.statut, Livrable.Statut.RENDU)
        self.client.post(url, {"action": "annuler"})
        self.livrable.refresh_from_db()
        self.assertEqual(self.livrable.statut, Livrable.Statut.A_RENDRE)

    def test_ecran_suivi_filtre_les_retards(self):
        self.client.force_login(self.career)
        with mock.patch("stages.views.aujourdhui", return_value=date(2027, 9, 20)):
            self.assertContains(self.client.get("/service-stages/suivi/?retard=1"), "Rapport de stage")
        with mock.patch("stages.views.aujourdhui", return_value=date(2027, 9, 1)):
            self.assertNotContains(self.client.get("/service-stages/suivi/?retard=1"), "Rapport de stage")
        self.client.force_login(self.etu3)
        self.assertEqual(self.client.get("/service-stages/suivi/").status_code, 403)

    def test_prolongation_remet_les_rappels_a_zero(self):
        envoyer_rappels(date(2027, 9, 8))
        self.assertEqual(self.livrable.rappels.count(), 1)
        self.assertEqual(prolonger_livrable(self.livrable, date(2027, 9, 30), par=self.career), [])
        self.assertEqual(self.livrable.rappels.count(), 0)
        self.livrable.refresh_from_db()
        self.assertEqual(self.livrable.date_limite, date(2027, 9, 30))
        self.assertTrue(prolonger_livrable(self.livrable, date(2027, 9, 1), par=self.career))   # date antérieure

    def test_l_etudiant_voit_ses_livrables_avec_le_lien_moodle(self):
        ModeleLivrable.objects.filter(type_stage="Technicien").update(lien_moodle="https://moodle.example.test/devoir/1")
        self.client.force_login(self.etu3)
        with mock.patch("stages.views.aujourdhui", return_value=date(2027, 9, 20)):
            page = self.client.get("/etudiant/mon-stage/").content.decode()
        self.assertIn("Mes livrables", page)
        self.assertIn("https://moodle.example.test/devoir/1", page)
        self.assertIn("En retard", page)
        self.assertNotIn("Déposer", page)          # plus de dépôt sur la plateforme : c'est sur Moodle


class RappelsTests(LivrableBase):
    """Rappels automatiques : date limite du rapport = 15/09/2027, calendrier par défaut 7, 3, 1 avant ; 1, 7 après."""

    def setUp(self):
        super().setUp()
        self.stage = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        creer_livrables(self.stage)
        self.livrable = self.stage.livrables.get()
        ModeleLivrable.objects.filter(type_stage="Technicien").update(lien_moodle="https://moodle.example.test/d/1")
        mail.outbox.clear()

    def test_calendrier_par_defaut_et_personnalise(self):
        self.assertEqual(ParametresEcole.actuels().decalages_rappels(), [7, 3, 1, -1, -7])
        ecole = ParametresEcole.actuels()
        ecole.rappels_avant, ecole.rappels_apres = "10, x, 2", ""
        self.assertEqual(ecole.decalages_rappels(), [10, 2])

    def test_aucun_rappel_trop_tot(self):
        self.assertEqual(envoyer_rappels(date(2027, 9, 1))["envoyes"], 0)       # 14 jours avant
        self.assertEqual(len(mail.outbox), 0)

    def test_un_rappel_a_7_jours_avec_le_lien_moodle(self):
        resultat = envoyer_rappels(date(2027, 9, 8))
        self.assertEqual(resultat["envoyes"], 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["adam@example.test"])
        self.assertIn("Rapport de stage", message.subject)
        self.assertIn("https://moodle.example.test/d/1", message.body)

    def test_jamais_deux_fois_le_meme_rappel(self):
        envoyer_rappels(date(2027, 9, 8))
        envoyer_rappels(date(2027, 9, 8))
        envoyer_rappels(date(2027, 9, 9))          # toujours dans la fenêtre « 7 jours »
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.livrable.rappels.count(), 1)

    def test_les_rappels_suivants_a_3_et_1_jours(self):
        for jour in (date(2027, 9, 8), date(2027, 9, 12), date(2027, 9, 14)):
            envoyer_rappels(jour)
        self.assertEqual(len(mail.outbox), 3)
        self.assertIn("demain", mail.outbox[2].subject)

    def test_un_seul_message_de_rattrapage_apres_plusieurs_jours_sans_commande(self):
        envoyer_rappels(date(2027, 9, 13))         # 2 jours avant : dus = 7 et 3 -> un seul e-mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(sorted(self.livrable.rappels.values_list("decalage", flat=True)), [3, 7])

    def test_aucun_rappel_si_le_livrable_est_rendu(self):
        marquer_rendu(self.livrable, par=self.career)
        self.assertEqual(envoyer_rappels(date(2027, 9, 14))["envoyes"], 0)
        self.assertEqual(envoyer_rappels(date(2027, 9, 30))["envoyes"], 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_retard_prevenant_l_etudiant_et_le_career_center(self):
        resultat = envoyer_rappels(date(2027, 9, 16))   # 1 jour de retard
        self.assertEqual(len(resultat["retards"]), 1)
        destinataires = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(destinataires, ["adam@example.test", ParametresEcole.actuels().email_contact])
        self.assertTrue(any("RETARD" in m.subject for m in mail.outbox))
        mail.outbox.clear()
        envoyer_rappels(date(2027, 9, 20))              # 5 jours de retard : rien de nouveau avant J+7
        self.assertEqual(len(mail.outbox), 0)
        envoyer_rappels(date(2027, 9, 22))              # 7 jours de retard
        self.assertEqual(len(mail.outbox), 2)

    def test_un_echec_d_envoi_est_retente_et_ne_bloque_pas_les_autres(self):
        autre = self.stage_valide(self.etu5, self.p5, date(2027, 2, 1), date(2027, 7, 31))
        creer_livrables(autre)
        mail.outbox.clear()

        def envoi_capricieux(sujet, corps, expediteur, destinataires, **kw):
            if destinataires == ["adam@example.test"]:
                raise OSError("serveur de messagerie indisponible")
            from django.core.mail import EmailMessage
            EmailMessage(sujet, corps, expediteur, destinataires).send()

        with mock.patch("stages.services.send_mail", side_effect=envoi_capricieux):
            resultat = envoyer_rappels(date(2027, 9, 14))
        self.assertEqual(resultat["erreurs"], 1)       # seul Adam est en erreur, Yasmine reçoit ses rappels
        self.assertEqual(self.livrable.rappels.count(), 0)            # rien d'enregistré : sera retenté
        self.assertEqual(envoyer_rappels(date(2027, 9, 14))["erreurs"], 0)
        self.assertEqual(self.livrable.rappels.count(), 3)

    def test_commande_et_date_invalide(self):
        sortie = StringIO()
        call_command("envoyer_rappels", "--date", "2027-09-08", stdout=sortie)
        self.assertIn("1 rappel(s) envoyé(s)", sortie.getvalue())
        with self.assertRaises(CommandError):
            call_command("envoyer_rappels", "--date", "pas-une-date", stdout=StringIO())

    def test_calendrier_modifiable_dans_les_parametres(self):
        ecole = ParametresEcole.actuels()
        ecole.rappels_avant = "10"
        ecole.save()
        self.assertEqual(envoyer_rappels(date(2027, 9, 6))["envoyes"], 1)     # 9 jours avant : fenêtre « 10 jours »
        self.assertEqual(list(self.livrable.rappels.values_list("decalage", flat=True)), [10])
