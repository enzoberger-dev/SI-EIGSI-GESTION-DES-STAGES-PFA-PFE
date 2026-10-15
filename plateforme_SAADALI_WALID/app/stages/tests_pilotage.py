"""
Tests du Lot 4 (pilotage et échanges). Lancer : python manage.py test
"""

import codecs
from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comptes import roles

from .csv_outils import ErreurCSV, ecrire_csv, lire_csv
from .echanges import exporter_conventions_signees, importer_webaurion, promotion_depuis_groupe
from .models import Convention, Inscription, Promotion, annee_universitaire_courante
from .tests import BaseStages, LivrableBase


def code_groupe(annee_etudes, suffixe=""):
    """Code de groupe WebAurion de l'année universitaire courante, ex. INGE_4_FISE_CA_2627."""
    debut = int(annee_universitaire_courante()[:4])
    return f"INGE_{annee_etudes}_FISE_CA_{debut % 100:02d}{(debut + 1) % 100:02d}{suffixe}"


def csv_octets(*lignes, entete="Nom;Prénom;E-mail;Code.Groupe;Rôle"):
    return ("\r\n".join([entete, *lignes]) + "\r\n").encode("utf-8-sig")


class OutilsCSVTests(TestCase):
    def test_lecture_avec_ou_sans_bom_et_les_deux_separateurs(self):
        for contenu in ("Nom;Prénom\nA;B\n".encode("utf-8-sig"), "Nom,Prénom\nA,B\n".encode("utf-8")):
            en_tetes, lignes = lire_csv(contenu)
            self.assertEqual(en_tetes, ["nom", "prenom"])
            self.assertEqual(lignes[0][1], {"nom": "A", "prenom": "B"})

    def test_lecture_windows_1252(self):
        _, lignes = lire_csv("Nom;Prénom\nÉlise;Zoé\n".encode("cp1252"))
        self.assertEqual(lignes[0][1]["nom"], "Élise")

    def test_fichier_invalide(self):
        with self.assertRaises(ErreurCSV):
            lire_csv(b"")
        with self.assertRaises(ErreurCSV):
            lire_csv(b"juste du texte sans separateur\n")

    def test_ecriture_excel_et_protection_des_formules(self):
        octets = ecrire_csv(["Sujet"], [["=1+1"], ["Normal"]])
        self.assertTrue(octets.startswith(b"\xef\xbb\xbf"))  # BOM : Excel affiche bien les accents
        texte = octets.decode("utf-8-sig")
        self.assertIn("'=1+1", texte)
        self.assertIn("Normal", texte)


class GroupeWebAurionTests(TestCase):
    def test_codes_reconnus(self):
        self.assertEqual(promotion_depuis_groupe("INGE_4_FISE_CA_2627"), (4, "2026-2027"))
        self.assertEqual(promotion_depuis_groupe("INGE_4_FISE_CA_2627_S7_EDS"), (4, "2026-2027"))
        self.assertEqual(promotion_depuis_groupe("INGE_1_FISE_CA_2324_TDB"), (1, "2023-2024"))
        # plusieurs groupes dans la même cellule : on prend le premier code reconnu
        self.assertEqual(promotion_depuis_groupe("P2028_E_CASA, INGE_3_FISE_CA_2526"), (3, "2025-2026"))

    def test_codes_refuses(self):
        for texte in ("", "P2028_E_CASA", "INGE_6_FISE_CA_2627", "INGE_4_FISE_CA_2629"):
            self.assertIsNone(promotion_depuis_groupe(texte), texte)


class ImportWebAurionTests(BaseStages):
    def test_cree_le_compte_et_l_inscription(self):
        rapport = importer_webaurion(csv_octets(f"Alaoui;Rania;rania.alaoui@example.test;{code_groupe(4)};Étudiant"))
        self.assertEqual(len(rapport.faits), 1)
        self.assertFalse(rapport.erreurs)
        compte = get_user_model().objects.get(email="rania.alaoui@example.test")
        self.assertEqual((compte.first_name, compte.last_name), ("Rania", "Alaoui"))
        self.assertTrue(compte.a_le_role(roles.ETUDIANT))
        self.assertTrue(compte.has_usable_password())
        inscription = compte.inscriptions.get()
        self.assertEqual(inscription.promotion.annee_etudes, 4)
        self.assertEqual(inscription.promotion.annee_universitaire, self.annee)
        # le mot de passe provisoire est donné au Career Center, et il fonctionne
        _email, _nom, mot_de_passe = rapport.comptes[0]
        self.assertTrue(compte.check_password(mot_de_passe))

    def test_le_role_est_facultatif_et_l_encadrant_n_a_pas_besoin_de_groupe(self):
        rapport = importer_webaurion(csv_octets(
            f"Idrissi;Hamza;hamza@example.test;{code_groupe(5)};",
            "Tazi;Leila;leila@example.test;;Encadrant",
        ))
        self.assertFalse(rapport.erreurs)
        self.assertTrue(get_user_model().objects.get(email="hamza@example.test").a_le_role(roles.ETUDIANT))
        encadrante = get_user_model().objects.get(email="leila@example.test")
        self.assertTrue(encadrante.a_le_role(roles.ENCADRANT))
        self.assertFalse(encadrante.inscriptions.exists())

    def test_deuxieme_import_identique_ne_change_rien(self):
        contenu = csv_octets(f"Alaoui;Rania;rania@example.test;{code_groupe(4)};")
        importer_webaurion(contenu)
        rapport = importer_webaurion(contenu)
        self.assertEqual((len(rapport.faits), len(rapport.ignorees), len(rapport.erreurs)), (0, 1, 0))
        self.assertEqual(get_user_model().objects.filter(email="rania@example.test").count(), 1)
        self.assertEqual(Inscription.objects.filter(etudiant__email="rania@example.test").count(), 1)

    def test_doublon_dans_le_fichier_et_casse_de_l_email(self):
        rapport = importer_webaurion(csv_octets(
            f"A;B;Double@Example.test;{code_groupe(4)};",
            f"A;B;double@example.test;{code_groupe(4, '_S7')};",
        ))
        self.assertEqual((len(rapport.faits), len(rapport.ignorees)), (1, 1))
        self.assertEqual(get_user_model().objects.filter(email="double@example.test").count(), 1)

    def test_compte_existant_jamais_modifie(self):
        rapport = importer_webaurion(csv_octets(f"Autre;Nom;adam@example.test;{code_groupe(3)};"))
        self.assertEqual(len(rapport.ignorees), 1)   # Adam est déjà inscrit en 3e cette année
        adam = get_user_model().objects.get(email="adam@example.test")
        self.assertEqual(adam.last_name, "Utilisateur")
        self.assertFalse(rapport.comptes)

    def test_compte_existant_dans_une_autre_promotion_est_signale(self):
        rapport = importer_webaurion(csv_octets(f"Adam;Test;adam@example.test;{code_groupe(5)};"))
        self.assertEqual(len(rapport.erreurs), 1)
        self.assertIn("déjà inscrit", rapport.erreurs[0][1])

    def test_une_ligne_en_erreur_n_empeche_pas_les_autres(self):
        rapport = importer_webaurion(csv_octets(
            f"Bon;Un;bon1@example.test;{code_groupe(4)};",
            f"Mauvais;Email;pas-un-email;{code_groupe(4)};",
            "Sans;Groupe;sans.groupe@example.test;;",
            f"Sans;;sans.prenom@example.test;{code_groupe(4)};",
            f"Role;Bizarre;role@example.test;{code_groupe(4)};Directeur",
            f"Bon;Deux;bon2@example.test;{code_groupe(4)};",
        ))
        self.assertEqual(len(rapport.faits), 2)
        self.assertEqual(sorted(numero for numero, _ in rapport.erreurs), [3, 4, 5, 6])
        utilisateurs = get_user_model().objects.values_list("email", flat=True)
        self.assertIn("bon2@example.test", utilisateurs)
        self.assertNotIn("sans.prenom@example.test", utilisateurs)   # la ligne refusée n'a rien laissé

    def test_simulation_n_enregistre_rien(self):
        avant = (get_user_model().objects.count(), Inscription.objects.count(), Promotion.objects.count())
        rapport = importer_webaurion(csv_octets(f"A;B;nouveau@example.test;{code_groupe(1)};"), simuler=True)
        self.assertEqual(len(rapport.faits), 1)
        self.assertTrue(rapport.simulation)
        apres = (get_user_model().objects.count(), Inscription.objects.count(), Promotion.objects.count())
        self.assertEqual(avant, apres)

    def test_colonnes_obligatoires_manquantes(self):
        with self.assertRaises(ErreurCSV):
            importer_webaurion(b"Nom;Prenom\nA;B\n")

    def test_titres_alternatifs_et_virgules(self):
        contenu = f"NOM,PRENOM,Courriel,Code groupe\nA,B,alt@example.test,{code_groupe(2)}\n".encode()
        self.assertEqual(len(importer_webaurion(contenu).faits), 1)

    def test_le_stage_de_l_etudiant_importe_se_deduit_de_sa_promotion(self):
        importer_webaurion(csv_octets(f"A;B;nouvelle@example.test;{code_groupe(5)};"))
        promotion = Inscription.objects.get(etudiant__email="nouvelle@example.test").promotion
        self.assertEqual(promotion.type_stage, "Fin d'Études")
        self.assertTrue(promotion.validation_par_encadrant)


class EcranImportWebAurionTests(BaseStages):
    def envoyer(self, contenu, **donnees):
        fichier = SimpleUploadedFile("export.csv", contenu, content_type="text/csv")
        return self.client.post(reverse("import_webaurion"), {"fichier": fichier, **donnees})

    def test_reserve_au_career_center(self):
        self.assertEqual(self.client.get(reverse("import_webaurion")).status_code, 302)  # non connecté
        for utilisateur in (self.etu3, self.encadrant, self.coordinateur):
            self.client.force_login(utilisateur)
            self.assertEqual(self.client.get(reverse("import_webaurion")).status_code, 403)
            self.assertEqual(self.envoyer(b"Nom;Prenom;Mail\nA;B;x@example.test\n").status_code, 403)
        self.assertFalse(get_user_model().objects.filter(email="x@example.test").exists())

    def test_import_reel_affiche_les_mots_de_passe_une_seule_fois(self):
        self.client.force_login(self.career)
        contenu = csv_octets(f"Alaoui;Rania;rania@example.test;{code_groupe(4)};")
        reponse = self.envoyer(contenu)   # pas de case « simuler » cochée : import réel
        self.assertContains(reponse, "rania@example.test")
        self.assertContains(reponse, "Mot de passe provisoire")
        self.assertIn("no-cache", reponse["Cache-Control"])
        reponse = self.envoyer(contenu)   # second envoi : plus aucun mot de passe affiché
        self.assertNotContains(reponse, "Mot de passe provisoire")

    def test_simulation_ne_montre_aucun_mot_de_passe(self):
        self.client.force_login(self.career)
        reponse = self.envoyer(csv_octets(f"A;B;sim@example.test;{code_groupe(4)};"), simuler="1")
        self.assertContains(reponse, "Simulation")
        self.assertNotContains(reponse, "Mot de passe provisoire")
        self.assertFalse(get_user_model().objects.filter(email="sim@example.test").exists())

    def test_fichier_invalide_donne_un_message_clair(self):
        self.client.force_login(self.career)
        reponse = self.envoyer(b"n'importe quoi")
        self.assertContains(reponse, "ne ressemble pas à un CSV")
        reponse = self.client.post(reverse("import_webaurion"), {})
        self.assertContains(reponse, "Choisissez un fichier CSV")


class ExportConventionsTests(LivrableBase):
    def convention(self, stage, statut, numero, **champs):
        return Convention.objects.create(stage=stage, numero=numero, statut=statut, **champs)

    def setUp(self):
        super().setUp()
        self.stage3 = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27),)
        self.stage5 = self.stage_valide(self.etu5, self.p5, date(2027, 2, 1), date(2027, 7, 30))
        self.signee = self.convention(self.stage3, Convention.Statut.SIGNEE, "2026-0001",
                                      signee_le=timezone.make_aware(datetime(2026, 12, 3, 10, 0)))
        self.convention(self.stage5, Convention.Statut.ENVOYEE, "2026-0002")

    def lire(self, octets):
        return lire_csv(octets)[1]

    def test_seules_les_conventions_signees_sont_exportees_au_format_webaurion(self):
        octets, nb = exporter_conventions_signees(self.annee)
        self.assertEqual(nb, 1)
        self.assertTrue(octets.startswith(codecs.BOM_UTF8))  # BOM : Excel affiche bien les accents
        _, lignes = lire_csv(octets)
        ligne = lignes[0][1]
        self.assertEqual(ligne["e mail"], "adam@example.test")
        self.assertEqual(ligne["n convention"], "2026-0001")
        self.assertEqual(ligne["debut"], "01/06/2027")
        self.assertEqual(ligne["fin"], "27/07/2027")
        self.assertEqual(ligne["libelle type de stage"], "Stage Technicien")
        self.assertEqual(ligne["entreprise"], "Atlas Énergies")
        self.assertEqual(ligne["validation service entreprise"], "Validé")
        self.assertEqual(ligne["validation pedagogique"], "Validé")
        self.assertEqual(ligne["validation du stage"], "")
        self.assertEqual(ligne["convention validee recue le"], "03/12/2026")

    def test_titres_identiques_a_ceux_de_webaurion(self):
        octets, _ = exporter_conventions_signees(self.annee)
        premiere_ligne = octets.decode("utf-8-sig").splitlines()[0].split(";")
        for titre in ("Début", "Fin", "Libellé.Type de stage", "Entreprise", "Sujet de stage",
                      "Validation service entreprise", "Validation pédagogique", "Validation du Stage",
                      "Convention validée reçue le"):
            self.assertIn(titre, premiere_ligne)

    def test_autre_annee_universitaire_vide(self):
        self.assertEqual(exporter_conventions_signees("2020-2021")[1], 0)

    def test_une_version_remplacee_n_est_pas_exportee(self):
        self.signee.statut = Convention.Statut.REMPLACEE
        self.signee.save()
        self.assertEqual(exporter_conventions_signees(self.annee)[1], 0)

    def test_sujet_malveillant_neutralise(self):
        self.stage3.sujet = "=HYPERLINK(\"http://exemple.test\")"
        self.stage3.save()
        texte = exporter_conventions_signees(self.annee)[0].decode("utf-8-sig")
        self.assertIn("'=HYPERLINK", texte)

    def test_telechargement_horodate_reserve_au_career_center(self):
        self.client.force_login(self.etu3)
        self.assertEqual(self.client.get(reverse("export_conventions")).status_code, 403)
        self.client.force_login(self.career)
        reponse = self.client.get(reverse("export_conventions"))
        self.assertEqual(reponse.status_code, 200)
        self.assertRegex(reponse["Content-Disposition"],
                         rf'attachment; filename="conventions-signees-{self.annee}-\d{{8}}-\d{{4}}\.csv"')
        self.assertIn("adam@example.test", reponse.content.decode("utf-8-sig"))
        # une année fantaisiste (tentative d'injection dans le nom du fichier) est ignorée
        reponse = self.client.get(reverse("export_conventions"), {"annee": 'x"; evil'})
        self.assertIn(self.annee, reponse["Content-Disposition"])
