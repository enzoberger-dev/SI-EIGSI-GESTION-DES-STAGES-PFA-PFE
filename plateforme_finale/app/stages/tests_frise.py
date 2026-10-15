"""Tests de la frise des étapes (lot 8) : on vérifie l'étape en cours et la prochaine action pour chaque situation."""

from types import SimpleNamespace as Objet

from django.test import SimpleTestCase

from . import frise


def etats(etapes):
    return [e.etat for e in etapes]


class FriseTests(SimpleTestCase):
    def test_pas_encore_de_stage(self):
        etapes, action = frise.calculer(None, None, [], None)
        self.assertEqual(etats(etapes), ["courant", "a-venir", "a-venir", "a-venir", "a-venir"])
        self.assertEqual(action.nom_url, "modifier_mon_stage")

    def test_brouillon_reste_a_la_premiere_etape(self):
        etapes, action = frise.calculer(Objet(statut="BROUILLON"), None, [], None)
        self.assertEqual(etapes[0].etat, "courant")
        self.assertIn("soumettez", action.titre.lower())

    def test_fiche_refusee_est_signalee(self):
        etapes, action = frise.calculer(Objet(statut="REFUSE"), None, [], None)
        self.assertEqual(etapes[0].etat, "refus")
        self.assertEqual(action.bouton, "Corriger ma fiche")

    def test_fiche_soumise_attend_la_validation(self):
        etapes, action = frise.calculer(Objet(statut="SOUMIS"), None, [], None)
        self.assertEqual(etats(etapes)[:3], ["fait", "courant", "a-venir"])
        self.assertEqual(action.bouton, "")  # rien à faire pour l'étudiant

    def test_stage_valide_sans_convention(self):
        etapes, action = frise.calculer(Objet(statut="VALIDE"), None, [], None)
        self.assertEqual(etats(etapes)[:3], ["fait", "fait", "courant"])
        self.assertEqual(action.bouton, "")

    def test_convention_envoyee_demande_le_scan(self):
        etapes, action = frise.calculer(Objet(statut="VALIDE"), Objet(statut="ENVOYEE"), [], None)
        self.assertEqual(etapes[2].etat, "courant")
        self.assertEqual(action.nom_url, "#convention")

    def test_convention_signee_ouvre_le_suivi(self):
        etapes, _ = frise.calculer(Objet(statut="VALIDE"), Objet(statut="SIGNEE"), [Objet(statut="A_RENDRE")], None)
        self.assertEqual(etats(etapes)[:4], ["fait", "fait", "fait", "courant"])

    def test_livrables_rendus_ouvrent_la_soutenance(self):
        etapes, action = frise.calculer(Objet(statut="VALIDE"), Objet(statut="SIGNEE"), [Objet(statut="RENDU")], None)
        self.assertEqual(etapes[4].etat, "courant")
        self.assertIn("soutenance", action.texte.lower())

    def test_dossier_termine(self):
        soutenance = Objet(statut="NOTEE", debut=None)
        etapes, action = frise.calculer(Objet(statut="VALIDE"), Objet(statut="SIGNEE"), [Objet(statut="RENDU")], soutenance)
        self.assertEqual(set(etats(etapes)), {"fait"})
        self.assertTrue(action.ok)

    def test_aucun_livrable_ne_compte_pas_comme_tout_rendu(self):
        etapes, _ = frise.calculer(Objet(statut="VALIDE"), Objet(statut="SIGNEE"), [], None)
        self.assertEqual(etapes[3].etat, "courant")
