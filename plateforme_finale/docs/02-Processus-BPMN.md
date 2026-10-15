# 02 — Processus (BPMN)

Retour : [[Accueil]] · Suite : [[03-Besoins-et-backlog]]

Les schémas BPMN 2.0 existent en PDF (`BPMN_TO-BE.pdf` sur le dépôt, 8 pages). Cette note donne leur contenu en texte pour que l'IA puisse le lire.

> **⚠️ Correction du 2026-10-12 (Walid) — prioritaire sur les schémas TO-BE ci-dessous.**
> La « validation à 3 niveaux » et le rôle **Responsable** venaient d'un malentendu : **il n'y a pas de Responsable** à l'école. Le processus réel est décrit dans la section suivante. Les schémas TO-BE 2, 2b et 5 sont à redessiner.

## Processus réel (source : Walid, 2026-10-12) — base du futur TO-BE
**Acteurs** : Étudiant · Encadrant (enseignant de l'école) · Service Stages · Directeur des études (signe pour l'école) · Tuteur de stage (dans l'entreprise, avec compte) · Jury (l'encadrant en fait-il partie ? à confirmer avec le prof).

**Aujourd'hui (AS-IS réel)** : l'étudiant remplit un formulaire sur WebAurion (entreprise, adresse, mission, dates…). Le Service Stages prépare la convention et l'envoie par e-mail à l'étudiant, **déjà signée par le directeur des études**. L'entreprise et l'étudiant la signent ensuite. D'après l'interview du Service Stages (Wael), cette étape est **lente** et doit être améliorée.

**Parcours cible :**
1. Le **Service Stages affecte un encadrant** à l'étudiant.
2. L'étudiant trouve un stage : par lui-même (Indeed, JobTeaser, réseau…), le cas le plus fréquent, ou grâce au Service Stages.
3. S'il l'a trouvé lui-même, il **soumet le stage à son encadrant**, qui le **valide ou le refuse** (motif obligatoire) selon son adéquation avec le cursus. C'est une validation **pédagogique du stage**, pas de la convention.
4. L'étudiant remplit les **informations de la convention**.
5. Le **Service Stages** produit la convention, **signée par le directeur des études**, et la transmet. La plateforme doit rendre cette étape rapide.
6. L'**entreprise** (tuteur) et l'**étudiant** signent.
7. Suite inchangée : suivi, livrables, rapport final, soutenance, notes, archivage.

**Questions ouvertes** (voir [[08-Decisions-ouvertes]]) : le formulaire WebAurion est-il remplacé par la plateforme ? Entreprise : liens uniques ou compte ?

### Précisions du 2026-10-12 (hypothèses de Walid + règlement des études EIGSI 2026-2027)
- **Le Service Stages s'appelle le Career Center** (adresse de contact `stages@…` sur la convention).
- **Tous les stages** passent par une validation avant la convention, y compris ceux trouvés via le Career Center.
- **Qui valide le stage, selon l'année** :
  - **4e et 5e année** : l'**encadrant** affecté à l'étudiant par le Career Center ;
  - **1re et 3e année** (et un éventuel stage d'initiative personnelle en 2e année) : le **coordinateur de promotion**.
  - Le règlement dit : sujets validés par les coordinateurs de promotion avant le début du stage ; par les coordinateurs d'options pour les stages Assistant-Ingénieur et Fin d'Études. *À confirmer avec le prof.*
- **Types de stage** (règlement, § III.8) : 1re Découverte (4 sem. min.) · 3e Technicien (6 sem.) · 4e Assistant-Ingénieur (12 sem.) · 5e Fin d'Études (24 sem., soutenance possible après 18 sem.). **PFE** = Projet de Fin d'Études (5e) ; **PFA** = Projet de Fin d'Année (autres années). *Hypothèse à confirmer.* Un étudiant fait un stage par an, donc plusieurs sur ses études.
- **Pas d'alternants à Casablanca** (constat de Walid) : la plateforme ne concerne que les étudiants.
- **Signatures sur papier** (pratique actuelle au Maroc) : la plateforme génère le PDF, le directeur des études signe en premier, puis l'entreprise, le tuteur et l'étudiant ; le scan signé est déposé sur la plateforme. Pas de signature électronique pour l'instant.
- **PFE** : l'entreprise remplit aussi une **évaluation des compétences** ; un plan directeur et un rapport sont à rendre.

## Processus actuel (AS-IS) — 3 schémas
1. **Recherche et validation de stage** (couloirs : Étudiant, Service Stages, Encadrant) : l'étudiant cherche un stage ; s'il n'en trouve pas, il demande de l'aide au Service Stages qui lui montre la base d'offres partenaires et le met en relation ; il passe un entretien ; puis il établit la convention et la dépose sur WebAurion.
2. **Suivi des documents de stage** (Service Stages, Étudiant, Encadrant) : vérification du dépôt de la convention, de sa conformité (durée, adresse, signatures) ; mails de rappel et de rectification ; validation de l'entreprise et affectation d'un encadrant ; dépôt de livrables et rapport ; 2 réunions de suivi minimum ; correction et note.
3. **Finalisation du stage** : fiche d'évaluation de l'entreprise, sondage de disponibilités, planning consolidé, convocations par mail, soutenance, PV signé, saisie de la note sur WebAurion, archivage.

Problèmes : e-mails dispersés, saisie répétée, aucune visibilité, relances manuelles.

## Processus cible (TO-BE) de la séance 2 — 5 schémas + un détail (en partie obsolète, voir la correction ci-dessus)
La plateforme (couloir « Plateforme ») automatise notifications, génération de documents, horodatage, relances et exports.

### TO-BE 1 — Déclaration et validation du stage (Étudiant, Encadrant, Plateforme)
Début de recherche → chercher un stage (réseau, sites d'emploi, offres partenaires) → stage trouvé ? → **déclarer ou corriger la fiche en ligne** → la plateforme notifie l'encadrant → l'encadrant **vérifie la conformité** → conforme ? non : retour à l'étudiant avec motif ; oui : **la plateforme génère la convention PDF** à partir de la fiche.

### TO-BE 2 — Convention : génération, validation, signature (Étudiant, Entreprise, Service Stages, Plateforme)
Convention générée → **validation hiérarchique à 3 niveaux** → validée ? non : l'étudiant corrige ; oui : **signature électronique tripartite** par liens uniques → trois signatures en parallèle (étudiant, entreprise, école) pendant que la plateforme **surveille les délais et relance par e-mail** → **export CSV vers WebAurion** → convention signée et exportée.

> **TO-BE 2 et 2b obsolètes (2026-10-12)** : pas de validation hiérarchique de la convention, pas de Responsable ; signature d'abord par l'école (directeur des études), puis par l'entreprise et l'étudiant.

### TO-BE 2b — Détail de la validation à 3 niveaux (obsolète)
Niveau 1 **Encadrant** → niveau 2 **Service Stages** → niveau 3 **Responsable**. À chaque niveau : valider ou refuser (**motif obligatoire** en cas de refus), la plateforme enregistre la décision (historique horodaté) et notifie le niveau suivant. Un refus arrête la chaîne et renvoie à l'étudiant. L'ordre exact est une hypothèse du groupe, à confirmer avec l'école.

### TO-BE 3 — Suivi du stage, livrables, rapport final (Étudiant, Encadrant, Service Stages, Plateforme)
Convention signée → en parallèle : **réunions de suivi** (minimum 2, fiches en ligne) et **relances automatiques** avant chaque date limite → dépôt d'un **livrable intermédiaire** → relecture et retour de l'encadrant → livrable validé ? (sinon nouveau dépôt) → tous les livrables remis ? → **dépôt du rapport final (PDF)**, horodaté et bloqué après la date limite → l'encadrant **corrige et évalue en ligne** → **tableau de bord** mis à jour → suivi clôturé.

### TO-BE 4 — Finalisation et soutenance (Étudiant, Jury, Entreprise, Service Stages, Plateforme)
Fin du stage → en parallèle : **grille d'évaluation de l'entreprise** (lien sécurisé) et **sondage de disponibilités** (étudiant, jury, salles) → **proposition automatique de créneaux** → le Service Stages **valide le planning** (sinon nouvelle proposition) → **convocations automatiques** → soutenance → le jury **remplit le PV en ligne** → le Service Stages **valide le PV et saisit la note** → **export des notes vers WebAurion (CSV)** et **archivage du dossier**.

### TO-BE 5 — Offres des entreprises partenaires (module optionnel) (Entreprise, Service Stages, Plateforme)
L'entreprise dépose une offre par formulaire public (sans compte) → le Responsable la **modère** *(2026-10-12 : la modération passe au Service Stages, et les entreprises auront un compte)* → conforme ? non : notification du refus ; oui : publication sur la plateforme.

## Remarques
- Le TO-BE 4 prévoit une grille d'évaluation de l'entreprise ; le backlog et le MCD de la séance 2 ne la couvrent pas (décision en cours : exclue du MVP, voir [[05-Donnees-MCD]]).
- Les schémas sources ont été générés en BPMN XML puis exportés ; leur modification se fait avec bpmn.io (outil recommandé par le cours).
