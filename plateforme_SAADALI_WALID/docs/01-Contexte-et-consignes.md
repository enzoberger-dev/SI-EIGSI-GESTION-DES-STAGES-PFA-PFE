# 01 — Contexte et consignes

Retour : [[Accueil]]

## Le cours
- **EIGSI Casablanca** — cours « Système d'information et transformation digitale », septembre-octobre 2026.
- Posture demandée par le prof : **consultants autonomes en entreprise**. Chaque séance produit un livrable poussé sur le dépôt GitHub du groupe.
- Sujet du groupe : **gestion des stages PFE/PFA** (stages d'ingénieur de fin d'études et de fin d'année).
- Dépôt GitHub du groupe (public) : `enzoberger-dev/SI-EIGSI-GESTION-DES-STAGES-PFA-PFE`. Contenu vu le 12/10 : `S1_Rapport…pdf`, `S2_Rapport…pdf`, `BPMN_TO-BE.pdf`, `Demo/`, `mvp_SAADALI_WALID/`, `démo wajih.zip`, `README.md`, `.gitignore`. Branches : `main`, `wajih-démo`.

## L'équipe
| Membre | Rôle en séance 1 |
|---|---|
| **SAADALI Walid** | Architecte Processus Métier : BPMN 2.0 AS-IS et TO-BE |
| **ADAWI Wael** | Consultant Analyste & Lead Besoins : entretien terrain, analyse stratégique, matrice MoSCoW |
| **BERGER Enzo** | Data & Governance Officer : KPI SMART, administration du dépôt GitHub, assemblage du livrable |
| Wajih (à confirmer) | 4e membre probable (branche `wajih-démo`) ; le rapport S1 ne liste que 3 noms |

Le groupe compte 4 personnes alors que la consigne parle de 3 maximum : **le prof a accepté le 4e membre** (voir [[08-Decisions-ouvertes]]).
En séance 2, Walid a fait le BPMN TO-BE, le modèle de données (MCD et dictionnaire) et mis en forme le rapport ; l'architecture a été reprise à partir du schéma du tableau blanc du groupe.

## Les séances
| Séance | Thème | Livrable | Statut |
|---|---|---|---|
| S1 | Cadrage : SWOT, alignement stratégique, BPMN AS-IS, MoSCoW, KPI SMART | `S1_Rapport_Gestion_des_stages_PFE_PFA.pdf` | rendu |
| S2 | Conception : user stories, maquettes, MCD + dictionnaire, architecture, BPMN TO-BE | `S2_Rapport…pdf`, message `MAJ GIT (Conception) : [lien]` | rendu (le texte du rapport garde l'ancienne stack, voir [[06-Architecture-et-stack]]) |
| S3 | MVP individuel avec VS Code + un agent IA | MVP dans son sous-dossier, vidéo de démo, message `MAJ GIT (MVP) : [lien]` | fait par Walid (voir [[07-MVP-demo-Copilot]]) |

## Consignes de la séance 3 (rappel)
- Chaque étudiant construit **son** MVP dans **son** sous-dossier (`mvp_SAADALI_WALID`), sur la branche `main`, sans toucher au README ni au `.gitignore` de la racine.
- Un rôle d'outil par étudiant (Gemini, Grok, Auto/Standard de GitHub Copilot). Walid a pris le rôle « étudiant 2 : Auto/Standard ». Le prof a précisé que **l'outil compte moins que l'objectif final**.
- Vidéo de démonstration par étudiant : `Nom_Prenom.mp4`, 100 Mo maximum, dans `demo/` à la racine.
- Un seul membre du groupe poste sur la plateforme du cours : `MAJ GIT (MVP) : [lien du dépôt]`, dépôt en Public.
- Méthode du prof : l'agent propose un **plan**, l'utilisateur répond « OK », puis l'agent agit. Étapes du document « Prompts prêts à copier-coller » : A1 lire la conception → A2 corriger le schéma → A3 définir le MVP (5 fonctionnalités max) → A4 installer la stack → B5 fichier d'instructions (`copilot-instructions.md`, équivalent de `CLAUDE.md`) → B6 agent « Développeur » → C7 squelette → C8 base de données → C9 une fonctionnalité à la fois → C10 tests → C11 bilan et scénario de démo de 3 minutes. Il fournit aussi des prompts de secours (erreur, régression, dérive, nouvelle session).

## Consignes S1 et S2 utiles
- S1 : mini-SWOT, alignement stratégique, interview flash de 5 minutes, matrice MoSCoW de 8 à 10 fonctionnalités, BPMN AS-IS, 3 à 4 KPI SMART.
- S2 : chaque tâche du BPMN TO-BE et chaque exigence MoSCoW devient une user story ; wireframes associés à un rôle (couloir BPMN) ; MCD + dictionnaire ; architecture technique.

## Alignement stratégique (rapport S1)
- **Axe 1** — Digitalisation de l'expérience étudiante : plus de papier, guichet unique en ligne 24h/24.
- **Axe 2** — Excellence opérationnelle, zéro perte d'information : fin des relances manuelles, alertes d'échéance automatiques.
- **Axe 3** — Réseau entreprises et traçabilité académique : annuaire des entreprises, évaluations des tuteurs centralisées, suivi de l'insertion professionnelle.

## SWOT du processus actuel (AS-IS, résumé)
- Forces : Service Stages réactif ; règle de 2 réunions de suivi minimum ; suivi personnalisé par les enseignants-chercheurs.
- Faiblesses : dépendance aux e-mails (pièces jointes perdues, pas d'historique) ; saisie manuelle répétée des conventions et PV ; aucun suivi en temps réel pour l'étudiant.
- Opportunités : guichet web unique ; relances automatiques ; tableau de bord de pilotage.
- Menaces : retards des entreprises ; risque juridique si une convention est perdue ou non signée ; plannings de soutenance difficiles à aligner.

## Fichiers sources à garder sous la main
Rapport S1, rapport S2, `BPMN_TO-BE.pdf` (dépôt GitHub) et le PDF des prompts du prof : copies dans `reference/` si présentes.
