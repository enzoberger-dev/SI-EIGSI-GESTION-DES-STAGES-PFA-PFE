# 05 — Données : MCD, dictionnaire, règles de gestion

Retour : [[Accueil]] · Fichiers : `reference/gestion_stages.sql` (MySQL), `reference/mcd_gestion_stages.dbml` (dbdiagram.io), `reference/mcd_merise.png`

Deux versions du modèle existent. Il faut choisir laquelle sert de base (voir [[08-Decisions-ouvertes]]).

## Version A — Modèle de la séance 2 (12 tables)
Couleurs du schéma : acteurs (gris), stage (bleu), convention (vert), livrables/rapport/soutenance (orange), offres (violet, optionnel).

| Table | Contenu et règles |
|---|---|
| `utilisateur` | nom, prénom, e-mail unique, rôle (ETUDIANT, ENCADRANT, SERVICE_STAGES, RESPONSABLE, JURY), mot de passe haché |
| `entreprise` | raison sociale, ville, contact (nom, e-mail obligatoire), téléphone — **sans compte** |
| `disponibilite` | créneaux (début, fin) cochés par les membres du jury |
| `stage` | étudiant, encadrant (deux lignes de `utilisateur`), entreprise, offre (facultative), origine (RESEAU, SITE_EMPLOI, OFFRE_PARTENAIRE), sujet, dates (fin après début), tuteur, `statut_conformite` (EN_ATTENTE, CONFORME, REFUSE) |
| `convention` | une seule par stage, numéro unique, PDF, statut (EN_VALIDATION, VALIDEE, EN_SIGNATURE, SIGNEE, REFUSEE) |
| `validation` | convention, valideur, niveau 1 à 3, décision (VALIDE/REFUSE), commentaire obligatoire si refus, date |
| `signature` | convention, signataire (ETUDIANT, ENTREPRISE, ECOLE), date, empreinte SHA-256 du PDF |
| `livrable` | stage, intitulé, date limite, fichier, statut (A_DEPOSER, DEPOSE, VALIDE, A_CORRIGER), commentaire |
| `rapport` | stage, PDF, date de dépôt, statut (DEPOSE, A_CORRIGER, CORRIGE), commentaire de l'encadrant |
| `soutenance` | une par stage, date/heure, salle, note (0 à 20), texte du PV, PV validé |
| `jury_soutenance` | table d'association : jurés ↔ soutenance (clé composée) |
| `offre` (optionnel) | intitulé, type PFA/PFE, description, lieu, statut (EN_MODERATION, PUBLIEE, REFUSEE), motif de refus obligatoire si refus, entreprise |

## Version B — Schéma corrigé de la séance 3 (proposé par l'agent, à relire)
Issu de la relecture critique faite avec Copilot. Il ajoute ou précise, notamment :
- `CANDIDATURE` (offre, étudiant, statut, message, lien facultatif vers le stage ; une candidature par étudiant et par offre) ;
- `VALIDATION_CONVENTION` avec une validation par niveau, `SIGNATURE_CONVENTION` avec une signature par type de signataire ;
- `LIVRABLE` + `DEPOT_LIVRABLE` et `DEPOT_RAPPORT_FINAL` : **chaque dépôt est une ligne** (les redépôts n'écrasent jamais l'historique) ; `EVALUATION_RAPPORT` par l'encadrant ;
- `CAMPAGNE_SOUTENANCE`, `DISPONIBILITE`, `SOUTENANCE` (PV saisi en formulaire, pas de fichier), `JURY_SOUTENANCE` ;
- `NOTIFICATION` (rappels, convocations, échecs d'envoi), `IMPORT_LOT` et `ERREUR_IMPORT` (rapport d'erreurs par ligne du CSV WebAurion).
Le texte complet est dans le dépôt GitHub : `mvp_SAADALI_WALID/docs/01-schema-corrige.md`. Ce n'est pas un script SQL.

## Incohérences relevées par la relecture (à ne pas oublier)
- Offres et candidatures : classées indispensables en S1, facultatives en S2.
- Évaluation du tuteur entreprise : prévue au BPMN, absente du backlog et des données.
- PV de soutenance : absent du dictionnaire S2 (la table `SOUTENANCE` n'a pas de champ PV dans le dictionnaire, alors que le script SQL et le DBML en ont).
- `jury_soutenance` sans entrée dans le dictionnaire.
- Signature : S1 demandait une signature électronique tripartite ; S2 propose horodatage + empreinte SHA-256, **sans certificat qualifié** (validation de l'école à obtenir).

## Changements à prévoir dans le modèle (relecture du 2026-10-12)
Suite au processus réel ([[02-Processus-BPMN]]) et à la relecture de Claude. **Rien n'est encore appliqué** : le modèle sera revu dans une étape dédiée, avec l'accord de Walid.
- **Rôles** : supprimer RESPONSABLE ; ajouter TUTEUR_ENTREPRISE (compte entreprise) et un moyen d'identifier le **directeur des études** comme signataire de l'école. Permettre **plusieurs rôles par personne** (l'encadrant pourrait être jury).
- **Affectation de l'encadrant** (US-23) par le Service Stages, avant la déclaration du stage : l'encadrant est lié à l'étudiant, pas seulement au stage.
- **Validation** : supprimer les niveaux 1 à 3 ; garder un historique des décisions (validation pédagogique du stage, contrôle de la convention).
- **Stage** : ajouter un statut BROUILLON / SOUMIS, le motif de refus, le type PFA/PFE, les missions, l'e-mail du tuteur, l'année universitaire, la date limite du rapport.
- **Convention** : gérer plusieurs versions (nouveau PDF après correction) ; signatures dans l'ordre école → entreprise et étudiant ; une seule signature par type de signataire.
- **Manques déjà repérés** : relances et notifications, rapport d'erreurs d'import, activation des comptes importés, salles, campagnes de soutenance, réunions de suivi, évaluation par l'entreprise, filière et promotion.

## ✅ Modèle proposé v2 (2026-10-12) — base de travail pour les Lots 1 et 2
Validé par Walid comme base de travail ; les points marqués *hypothèse* sont à confirmer avec le prof.

```
Promotion ── coordinateur ──► Utilisateur        (ex. « 3e année 2026-2027 »)
   ▲
   │ inscrit dans
Étudiant (Utilisateur)
   ├── Affectation ──► Encadrant                 (4e et 5e année seulement)
   └── Stage ──► Entreprise
         ├── Historique   (soumission, validation, refus + motif…)
         └── Convention   (versions, PDF généré, scan signé, dates de signature)
Paramètres de l'école (modifiables par le Career Center)
```

| Table | Contenu | Règles |
|---|---|---|
| **Promotion** | année d'études (1 à 5), année universitaire, coordinateur, volume horaire de l'année | une promotion par année d'études et par année universitaire |
| **Inscription** (ou champ sur l'étudiant) | étudiant → promotion | un étudiant dans une seule promotion par année universitaire |
| **Affectation** | étudiant, encadrant, année universitaire, affecté par, date, active | 4e et 5e année seulement ; une seule affectation active par étudiant et par année ; un changement crée une nouvelle ligne (historique) |
| **Entreprise** | raison sociale, adresse, code postal, ville, pays, téléphone, e-mail de contact | réutilisée d'un stage à l'autre (annuaire des entreprises, prévu par l'art. 13 de la convention) |
| **Stage** (la fiche) | étudiant, promotion, entreprise, origine (réseau, site d'emploi, Career Center, offre partenaire), **type** (déduit de l'année : Découverte, Initiative personnelle, Technicien, Assistant-Ingénieur, Fin d'Études), sujet et activités confiées, lieu du stage s'il est différent, représentant de l'entreprise (nom, fonction), tuteur (nom, e-mail, téléphone), dates, heures max par semaine, horaires, cas particuliers (nuit, dimanche, férié), gratification (montant, modalités), avantages en nature, statut, date limite du rapport | statut BROUILLON → SOUMIS → VALIDÉ ou REFUSÉ (motif obligatoire), puis correction et nouvelle soumission ; date de fin après la date de début ; **durée minimale selon le type** ; un stage par étudiant et par année universitaire |
| **Historique** | stage, auteur, action, commentaire, date et heure | une seule table pour tout le fil du dossier ; motif obligatoire pour un refus |
| **Convention** | stage, numéro unique, version, PDF généré, **scan signé**, statut, dates de signature : école, entreprise, tuteur, étudiant | une nouvelle version ne remplace jamais l'ancienne (statut REMPLACÉE) ; signature de l'école en premier |
| **Paramètres de l'école** | nom, adresse, représentant, directeur des études, e-mail et téléphone de contact | modifiables sans toucher au code |

**Valideur du stage** : l'encadrant de l'affectation active en 4e et 5e année ; le coordinateur de la promotion en 1re, 2e et 3e année. *Hypothèse.*
**Nouveau rôle** : « Coordinateur de promotion » (cumulable avec Encadrant ou Jury).
**Supprimé** : la table Signature (signatures sur papier, scan déposé).
**Plus tard** : livrables (dont plan directeur), dépôts du rapport, évaluation des compétences par l'entreprise (PFE), soutenances, disponibilités, salles, notifications, imports CSV.

### Structure de la convention EIGSICA (relevée sur un exemplaire réel, sans données personnelles)
- **Titre** selon le type (« CONVENTION Stage Technicien »…).
- **Art. 1, parties** : organisme d'accueil (raison sociale, adresse, lieu du stage s'il est différent, représentant et sa fonction, tuteur) ; école (fixe) ; étudiant (nom, année d'études, cursus, volume horaire de l'année) ; sujet et activités confiées.
- **Art. 2, objectif** : texte fixe (référentiel de compétences).
- **Art. 3, modalités** : dates, durée en mois, heures max par semaine, horaires, cas particuliers.
- **Art. 4, encadrement** : texte fixe + modalités propres au type (Technicien : auto-évaluation intermédiaire, rapport relu par le tuteur avant envoi au Career Center).
- **Art. 5, gratification** (non obligatoire), modalités de versement, avantages en nature. **Art. 6** : couverture maladie oui/non (cochée par l'entreprise). **Art. 7 à 12** : textes fixes.
- **Art. 13, données personnelles** : conservation **10 ans** ; constitution d'une liste des entreprises d'accueil ; droits d'accès via `stages@…`.
- **Signatures** : directeur de l'entreprise, directeur des études (signe et tamponne en premier), étudiant, tuteur de l'entreprise.

## Règles de gestion à respecter dans le code
1. Un stage → une convention maximum → une soutenance maximum (pas de rattrapage en MVP).
2. La convention n'est générée que si le stage est **conforme**.
3. ~~Validations dans l'ordre Encadrant > Service Stages > Responsable~~ *(abandonné le 2026-10-12)* : l'encadrant valide le **stage** (motif obligatoire si refus), puis le Service Stages émet la convention signée par le directeur des études ; historique horodaté.
4. Signature de l'école d'abord, puis l'entreprise et l'étudiant ; la convention est ensuite verrouillée.
5. Rapport final : PDF uniquement, horodaté, **dépôt bloqué après la date limite** ; historique conservé.
6. Note de soutenance entre 0 et 20 ; PV validé par le Service Stages avant export.
7. Entreprise sans compte : accès par **lien unique** envoyé par e-mail.
8. Imports/exports WebAurion en **CSV** avec rapport d'erreurs ligne par ligne, sans doublons.
9. Le tableau de bord se calcule à partir des statuts et dates (pas de table dédiée).
