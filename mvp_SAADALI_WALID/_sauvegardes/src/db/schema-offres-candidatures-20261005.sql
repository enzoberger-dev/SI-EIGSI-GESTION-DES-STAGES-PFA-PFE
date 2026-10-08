PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS UTILISATEUR (
  id_utilisateur INTEGER PRIMARY KEY,
  nom TEXT NOT NULL,
  prenom TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL CHECK (role IN ('ETUDIANT', 'ENCADRANT', 'SERVICE_STAGES', 'RESPONSABLE', 'JURY')),
  password_hash TEXT
);

CREATE TABLE IF NOT EXISTS AFFECTATION_ENCADRANT (
  id_affectation INTEGER PRIMARY KEY,
  id_etudiant INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  id_encadrant INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  id_agent INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  statut TEXT NOT NULL DEFAULT 'EN_ATTENTE'
    CHECK (statut IN ('EN_ATTENTE', 'UTILISEE', 'ANNULEE')),
  date_affectation TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS affectation_unique_en_attente_par_etudiant
  ON AFFECTATION_ENCADRANT (id_etudiant)
  WHERE statut = 'EN_ATTENTE';

CREATE TABLE IF NOT EXISTS ENTREPRISE (
  id_entreprise INTEGER PRIMARY KEY,
  raison_sociale TEXT NOT NULL,
  ville TEXT NOT NULL,
  contact_email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS OFFRE (
  id_offre INTEGER PRIMARY KEY,
  id_entreprise INTEGER NOT NULL REFERENCES ENTREPRISE(id_entreprise),
  type TEXT NOT NULL CHECK (type IN ('PFA', 'PFE')),
  titre TEXT NOT NULL,
  description TEXT NOT NULL,
  ville TEXT NOT NULL,
  duree_mois INTEGER NOT NULL CHECK (duree_mois > 0),
  statut TEXT NOT NULL DEFAULT 'EN_MODERATION'
    CHECK (statut IN ('EN_MODERATION', 'PUBLIEE', 'REFUSEE')),
  motif_refus TEXT,
  date_creation TEXT NOT NULL,
  date_moderation TEXT,
  CHECK (statut != 'REFUSEE' OR length(trim(motif_refus)) > 0)
);

CREATE TABLE IF NOT EXISTS STAGE (
  id_stage INTEGER PRIMARY KEY,
  id_etudiant INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  id_encadrant INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  id_entreprise INTEGER NOT NULL REFERENCES ENTREPRISE(id_entreprise),
  id_offre INTEGER REFERENCES OFFRE(id_offre),
  type TEXT NOT NULL CHECK (type IN ('PFA', 'PFE')),
  sujet TEXT NOT NULL,
  description TEXT NOT NULL,
  ville TEXT NOT NULL,
  origine TEXT NOT NULL CHECK (origine IN ('RESEAU', 'SITE_EMPLOI', 'OFFRE_PARTENAIRE')),
  nom_tuteur_entreprise TEXT NOT NULL,
  email_tuteur_entreprise TEXT NOT NULL,
  date_debut TEXT NOT NULL,
  date_fin TEXT NOT NULL,
  statut_conformite TEXT NOT NULL DEFAULT 'EN_ATTENTE'
    CHECK (statut_conformite IN ('EN_ATTENTE', 'CONFORME', 'REFUSE')),
  motif_refus TEXT,
  statut_dossier TEXT NOT NULL DEFAULT 'RECHERCHE'
    CHECK (statut_dossier IN ('RECHERCHE', 'CONVENTION', 'EN_COURS', 'RAPPORT', 'TERMINE')),
  CHECK (date_fin > date_debut),
  CHECK (statut_conformite != 'REFUSE' OR length(trim(motif_refus)) > 0),
  CHECK ((origine = 'OFFRE_PARTENAIRE' AND id_offre IS NOT NULL) OR
         (origine != 'OFFRE_PARTENAIRE' AND id_offre IS NULL))
);

CREATE TABLE IF NOT EXISTS BROUILLON_STAGE (
  id_brouillon INTEGER PRIMARY KEY,
  id_etudiant INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  id_affectation INTEGER NOT NULL UNIQUE REFERENCES AFFECTATION_ENCADRANT(id_affectation),
  id_stage INTEGER UNIQUE REFERENCES STAGE(id_stage),
  entreprise TEXT,
  ville TEXT,
  origine TEXT CHECK (origine IS NULL OR origine IN ('RESEAU', 'SITE_EMPLOI', 'OFFRE_PARTENAIRE')),
  id_offre INTEGER REFERENCES OFFRE(id_offre),
  sujet TEXT,
  type TEXT CHECK (type IS NULL OR type IN ('PFA', 'PFE')),
  date_debut TEXT,
  date_fin TEXT,
  nom_tuteur_entreprise TEXT,
  email_tuteur_entreprise TEXT,
  missions TEXT,
  statut TEXT NOT NULL DEFAULT 'BROUILLON'
    CHECK (statut IN ('BROUILLON', 'SOUMIS')),
  date_modification TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS VALIDATION_STAGE (
  id_validation_stage INTEGER PRIMARY KEY,
  id_stage INTEGER NOT NULL REFERENCES STAGE(id_stage),
  id_validateur INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  decision TEXT NOT NULL CHECK (decision IN ('CONFORME', 'REFUSE')),
  commentaire TEXT,
  date_decision TEXT NOT NULL,
  CHECK (decision != 'REFUSE' OR length(trim(commentaire)) > 0)
);

CREATE TABLE IF NOT EXISTS CANDIDATURE (
  id_candidature INTEGER PRIMARY KEY,
  id_offre INTEGER NOT NULL REFERENCES OFFRE(id_offre),
  id_etudiant INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  id_stage INTEGER UNIQUE REFERENCES STAGE(id_stage),
  date_candidature TEXT NOT NULL,
  statut TEXT NOT NULL DEFAULT 'EN_ATTENTE'
    CHECK (statut IN ('EN_ATTENTE', 'RETENUE', 'REFUSEE', 'RETIRÉE')),
  message TEXT,
  UNIQUE (id_offre, id_etudiant)
);

CREATE TABLE IF NOT EXISTS CONVENTION (
  id_convention INTEGER PRIMARY KEY,
  id_stage INTEGER NOT NULL UNIQUE REFERENCES STAGE(id_stage),
  numero TEXT NOT NULL UNIQUE,
  pdf_path TEXT,
  statut TEXT NOT NULL DEFAULT 'EN_VALIDATION'
    CHECK (statut IN ('EN_VALIDATION', 'VALIDEE', 'EN_SIGNATURE', 'SIGNEE', 'REFUSEE')),
  date_creation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS VALIDATION_CONVENTION (
  id_validation INTEGER PRIMARY KEY,
  id_convention INTEGER NOT NULL REFERENCES CONVENTION(id_convention),
  id_validateur INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  niveau INTEGER NOT NULL CHECK (niveau BETWEEN 1 AND 3),
  decision TEXT NOT NULL CHECK (decision IN ('VALIDE', 'REFUSE')),
  commentaire TEXT,
  date_decision TEXT NOT NULL,
  UNIQUE (id_convention, niveau),
  CHECK (decision != 'REFUSE' OR length(trim(commentaire)) > 0)
);

CREATE TABLE IF NOT EXISTS SIGNATURE_CONVENTION (
  id_signature INTEGER PRIMARY KEY,
  id_convention INTEGER NOT NULL REFERENCES CONVENTION(id_convention),
  signataire TEXT NOT NULL CHECK (signataire IN ('ETUDIANT', 'ENTREPRISE', 'ECOLE')),
  id_signataire INTEGER REFERENCES UTILISATEUR(id_utilisateur),
  email_signataire TEXT,
  empreinte_sha256 TEXT,
  date_signature TEXT,
  UNIQUE (id_convention, signataire)
);

CREATE TABLE IF NOT EXISTS LIVRABLE (
  id_livrable INTEGER PRIMARY KEY,
  id_stage INTEGER NOT NULL REFERENCES STAGE(id_stage),
  nom TEXT NOT NULL,
  date_limite TEXT NOT NULL,
  UNIQUE (id_stage, nom)
);

CREATE TABLE IF NOT EXISTS DEPOT_LIVRABLE (
  id_depot INTEGER PRIMARY KEY,
  id_livrable INTEGER NOT NULL REFERENCES LIVRABLE(id_livrable),
  fichier_path TEXT NOT NULL,
  date_depot TEXT NOT NULL,
  statut TEXT NOT NULL DEFAULT 'DEPOSE'
    CHECK (statut IN ('DEPOSE', 'A_CORRIGER', 'VALIDE')),
  commentaire TEXT
);

CREATE TABLE IF NOT EXISTS DEPOT_RAPPORT_FINAL (
  id_depot_rapport INTEGER PRIMARY KEY,
  id_stage INTEGER NOT NULL REFERENCES STAGE(id_stage),
  fichier_path TEXT NOT NULL,
  date_depot TEXT NOT NULL,
  statut TEXT NOT NULL DEFAULT 'DEPOSE'
    CHECK (statut IN ('DEPOSE', 'A_CORRIGER', 'CORRIGE')),
  commentaire_encadrant TEXT
);

CREATE TABLE IF NOT EXISTS EVALUATION_RAPPORT (
  id_evaluation INTEGER PRIMARY KEY,
  id_depot_rapport INTEGER NOT NULL UNIQUE REFERENCES DEPOT_RAPPORT_FINAL(id_depot_rapport),
  id_encadrant INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  commentaire TEXT NOT NULL,
  note NUMERIC CHECK (note IS NULL OR note BETWEEN 0 AND 20),
  date_evaluation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS CAMPAGNE_SOUTENANCE (
  id_campagne INTEGER PRIMARY KEY,
  nom TEXT NOT NULL,
  date_debut TEXT NOT NULL,
  date_fin TEXT NOT NULL,
  CHECK (date_fin >= date_debut)
);

CREATE TABLE IF NOT EXISTS DISPONIBILITE (
  id_disponibilite INTEGER PRIMARY KEY,
  id_campagne INTEGER NOT NULL REFERENCES CAMPAGNE_SOUTENANCE(id_campagne),
  id_jure INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  debut TEXT NOT NULL,
  fin TEXT NOT NULL,
  CHECK (fin > debut),
  UNIQUE (id_campagne, id_jure, debut, fin)
);

CREATE TABLE IF NOT EXISTS SOUTENANCE (
  id_soutenance INTEGER PRIMARY KEY,
  id_stage INTEGER NOT NULL UNIQUE REFERENCES STAGE(id_stage),
  id_campagne INTEGER REFERENCES CAMPAGNE_SOUTENANCE(id_campagne),
  date_heure TEXT,
  salle TEXT,
  note NUMERIC CHECK (note IS NULL OR note BETWEEN 0 AND 20),
  pv_texte TEXT,
  statut_pv TEXT NOT NULL DEFAULT 'A_SAISIR'
    CHECK (statut_pv IN ('A_SAISIR', 'A_VALIDER', 'VALIDE')),
  id_validateur INTEGER REFERENCES UTILISATEUR(id_utilisateur),
  date_validation TEXT
);

CREATE TABLE IF NOT EXISTS JURY_SOUTENANCE (
  id_soutenance INTEGER NOT NULL REFERENCES SOUTENANCE(id_soutenance),
  id_jure INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  PRIMARY KEY (id_soutenance, id_jure)
);

CREATE TABLE IF NOT EXISTS NOTIFICATION (
  id_notification INTEGER PRIMARY KEY,
  id_destinataire INTEGER REFERENCES UTILISATEUR(id_utilisateur),
  email_destinataire TEXT NOT NULL,
  type TEXT NOT NULL,
  date_prevue TEXT,
  date_envoi TEXT,
  resultat TEXT NOT NULL DEFAULT 'A_ENVOYER'
    CHECK (resultat IN ('A_ENVOYER', 'ENVOYEE', 'ECHEC')),
  reference_type TEXT,
  reference_id INTEGER
);

CREATE TABLE IF NOT EXISTS IMPORT_LOT (
  id_import INTEGER PRIMARY KEY,
  id_utilisateur INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
  nom_fichier TEXT NOT NULL,
  date_import TEXT NOT NULL,
  statut TEXT NOT NULL CHECK (statut IN ('EN_COURS', 'TERMINE', 'ECHEC'))
);

CREATE TABLE IF NOT EXISTS ERREUR_IMPORT (
  id_erreur INTEGER PRIMARY KEY,
  id_import INTEGER NOT NULL REFERENCES IMPORT_LOT(id_import),
  numero_ligne INTEGER NOT NULL CHECK (numero_ligne > 0),
  message TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS verifier_candidature_stage_insert
BEFORE INSERT ON CANDIDATURE
WHEN NEW.id_stage IS NOT NULL
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM STAGE
    WHERE id_stage = NEW.id_stage
      AND id_etudiant = NEW.id_etudiant
      AND id_offre = NEW.id_offre
  ) THEN RAISE(ABORT, 'La candidature et le stage doivent avoir le meme etudiant et la meme offre') END;
END;

CREATE TRIGGER IF NOT EXISTS verifier_candidature_stage_update
BEFORE UPDATE OF id_offre, id_etudiant, id_stage ON CANDIDATURE
WHEN NEW.id_stage IS NOT NULL
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM STAGE
    WHERE id_stage = NEW.id_stage
      AND id_etudiant = NEW.id_etudiant
      AND id_offre = NEW.id_offre
  ) THEN RAISE(ABORT, 'La candidature et le stage doivent avoir le meme etudiant et la meme offre') END;
END;
