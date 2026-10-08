INSERT OR IGNORE INTO UTILISATEUR (id_utilisateur, nom, prenom, email, role) VALUES
  (1, 'Benali', 'Yasmine', 'yasmine.benali@example.test', 'ETUDIANT'),
  (2, 'El Amrani', 'Adam', 'adam.elamrani@example.test', 'ETUDIANT'),
  (3, 'Bennani', 'Sara', 'sara.bennani@example.test', 'ENCADRANT'),
  (4, 'Alaoui', 'Nadia', 'nadia.alaoui@example.test', 'SERVICE_STAGES'),
  (5, 'Idrissi', 'Karim', 'karim.idrissi@example.test', 'RESPONSABLE'),
  (6, 'Tazi', 'Meryem', 'meryem.tazi@example.test', 'JURY');

INSERT OR IGNORE INTO ENTREPRISE (id_entreprise, raison_sociale, ville, contact_email) VALUES
  (1, 'Atlas Energies', 'Casablanca', 'stages@atlas-energies.example.test'),
  (2, 'Medina Digital', 'Rabat', 'recrutement@medina-digital.example.test');

INSERT OR IGNORE INTO COMPTE_ENTREPRISE
  (id_compte, id_entreprise, nom, prenom, email)
VALUES
  (1, 1, 'Mansouri', 'Nora', 'nora.mansouri@atlas-energies.example.test');

INSERT OR IGNORE INTO OFFRE
  (id_offre, id_entreprise, type, titre, description, ville, duree_mois, statut, date_creation, date_moderation)
VALUES
  (1, 1, 'PFE', 'Optimisation énergétique des bâtiments', 'Étudier des pistes de réduction de consommation énergétique.', 'Casablanca', 6, 'PUBLIEE', '2026-09-15', '2026-09-16'),
  (2, 2, 'PFA', 'Tableau de bord de suivi de production', 'Créer une maquette de suivi des indicateurs industriels.', 'Rabat', 3, 'PUBLIEE', '2026-09-20', '2026-09-21');

INSERT OR IGNORE INTO STAGE
  (id_stage, id_etudiant, id_encadrant, id_entreprise, id_offre, type, sujet, description, ville, origine, nom_tuteur_entreprise, email_tuteur_entreprise, date_debut, date_fin, statut_conformite, statut_dossier)
VALUES
  (1, 1, 3, 1, 1, 'PFE', 'Optimisation énergétique d’un bâtiment tertiaire', 'Mesurer les consommations et proposer des améliorations adaptées.', 'Casablanca', 'OFFRE_PARTENAIRE', 'Amine Berrada', 'amine.berrada@atlas-energies.example.test', '2026-11-01', '2027-04-30', 'CONFORME', 'CONVENTION'),
  (2, 2, 3, 2, NULL, 'PFA', 'Suivi numérique de la production', 'Concevoir un prototype de suivi pour une ligne de production.', 'Rabat', 'RESEAU', 'Salma Naciri', 'salma.naciri@medina-digital.example.test', '2026-10-01', '2027-01-31', 'EN_ATTENTE', 'RECHERCHE');

INSERT OR IGNORE INTO CANDIDATURE
  (id_candidature, id_offre, id_etudiant, id_stage, date_candidature, statut, message)
VALUES
  (1, 1, 1, 1, '2026-09-18', 'RETENUE', 'Candidature retenue pour le PFE.'),
  (2, 2, 1, NULL, '2026-09-22', 'EN_ATTENTE', 'Intéressée par le suivi numérique de production.');

INSERT OR IGNORE INTO CONVENTION (id_convention, id_stage, numero, statut, date_creation) VALUES
  (1, 1, 'CONV-2026-001', 'EN_VALIDATION', '2026-10-01');

INSERT OR IGNORE INTO VALIDATION_CONVENTION
  (id_validation, id_convention, id_validateur, niveau, decision, commentaire, date_decision)
VALUES
  (1, 1, 3, 1, 'VALIDE', 'Sujet conforme au cursus.', '2026-10-02');

INSERT OR IGNORE INTO LIVRABLE (id_livrable, id_stage, nom, date_limite) VALUES
  (1, 1, 'Plan de travail', '2026-11-20');

INSERT OR IGNORE INTO DEPOT_RAPPORT_FINAL
  (id_depot_rapport, id_stage, fichier_path, date_depot, statut, commentaire_encadrant)
VALUES
  (1, 2, 'uploads/demo/rapport-pfa.pdf', '2026-10-04', 'A_CORRIGER', 'Ajouter une description plus précise de la méthode.');

INSERT OR IGNORE INTO EVALUATION_RAPPORT
  (id_evaluation, id_depot_rapport, id_encadrant, commentaire, note, date_evaluation)
VALUES
  (1, 1, 3, 'Première lecture effectuée ; des précisions sont demandées.', NULL, '2026-10-05');
