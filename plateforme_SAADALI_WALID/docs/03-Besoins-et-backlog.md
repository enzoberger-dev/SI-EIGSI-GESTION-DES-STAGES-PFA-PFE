# 03 — Besoins et backlog

Retour : [[Accueil]] · Processus d'origine : [[02-Processus-BPMN]] · Écrans : [[04-Maquettes-UX]] · Données : [[05-Donnees-MCD]]

## KPI SMART du groupe (rapport S1, Enzo)
| KPI | Objectif | Cible |
|---|---|---|
| Temps de chargement | une requête se termine vite | 10 s maximum, quelle que soit la requête |
| Rappels / alertes | prévenir l'étudiant des tâches avant la date butoire (notification par mois, semaine ou jour) | moins de 10 rappels sur l'ensemble des étudiants |
| Coût de maintenance | rester dans un budget | 2000 € maximum |

Intention : gagner du temps sur le traitement des dossiers et offrir une expérience fluide.

## Matrice MoSCoW — état
- La matrice du rapport S1 (Wael) classait les offres d'entreprises et la candidature des étudiants parmi les indispensables.
- Depuis, le groupe a réorienté le produit : les étudiants trouvent leur stage ailleurs, donc les offres passent en **Could** (module optionnel). Livrables intermédiaires et correction du rapport par l'encadrant passent en **Should**.
- Walid doit encore **aligner la matrice avec Wael** (voir [[08-Decisions-ouvertes]]).
- Contexte à garder : dans la réalité actuelle de l'école, la convention est établie dans WebAurion ; la plateforme doit faire la saisie de la fiche et générer le PDF.

## ⚠️ Correction du 2026-10-14 : les livrables sont rendus sur MOODLE
Source : Walid, confirmé par le « Guide des stages et des expériences professionnelles 2025-2026 » (livret 1). Le dépôt des livrables sur Moodle n'est pas modifiable. Conséquences sur le backlog :
- **US-09** (dépôt du rapport sur la plateforme), **US-17** (dépôt des livrables), **US-18** (validation d'un livrable) et **US-19** (correction et évaluation du rapport) sont **abandonnées** : tout se passe sur Moodle.
- **US-10 devient la fonction centrale** : « en tant qu'agent du Career Center, je veux que la plateforme **rappelle automatiquement** aux étudiants leurs livrables à rendre sur Moodle (7, 3 et 1 jour avant, puis en cas de retard), afin de ne plus relancer à la main ». Critères : calendrier réglable ; lien Moodle dans le message ; arrêt dès que le Career Center a marqué le livrable « rendu » ; chaque rappel tracé et jamais envoyé deux fois ; récapitulatif des retards au Career Center.
- **US-11** (tableau de bord) : « rapports déposés » devient « livrables rendus (marqués par le Career Center) ».
- Le statut « rendu » est saisi **à la main** par le Career Center : seule partie manuelle restante, tant qu'il n'y a pas de lien (export CSV ou connexion) avec Moodle.
- Livrables attendus (guide) : 1re et 3e année = rapport ; 4e année = plan directeur (+3 semaines), rapport, évaluation des compétences signée par l'entreprise (fin + 2 semaines) ; 5e année = plan directeur (+4 semaines), rapport, évaluation des compétences, plan et support de soutenance.

## ⚠️ Corrections du 2026-10-12 (processus réel, voir [[02-Processus-BPMN]])
- **Le rôle Responsable n'existe pas.** Ses tâches passent au **Service Stages** (US-11 tableau de bord, US-21 modération des offres).
- **US-04 réécrite** : plus de validation de la convention à 3 niveaux. Le Service Stages émet la convention signée par le directeur des études *(proposition de Claude, à valider)*.
- **US-05** : signature **séquentielle**, l'école (directeur des études) d'abord, puis l'entreprise et l'étudiant.
- **US-02** : c'est la validation **pédagogique** du stage par l'encadrant. Elle s'applique au moins aux stages trouvés par l'étudiant lui-même (pour ceux trouvés via le Service Stages : à confirmer).
- **Nouvelle US-23 (Must)** : affectation de l'encadrant par le Service Stages.
- **Entreprises avec compte** (tuteur de stage), au lieu des liens uniques : décision de principe, à affiner. Concerne US-05, US-20, US-21 et l'évaluation par l'entreprise.
- Total après correction : **23 user stories (17 Must, 3 Should, 3 Could)**.

## Backlog (rapport S2, corrigé le 2026-10-12)
Le MVP compte **16 user stories Must** issues du BPMN TO-BE (schémas 1 à 5). Les étudiants trouvent leur stage hors de la plateforme (réseau, sites d'emploi) : la plateforme simplifie la gestion du stage pour les étudiants, les encadrants et le Service Stages. Les offres des entreprises partenaires restent un module optionnel.

## Priorités et schémas

- **Must (17 depuis l'ajout de US-23)** : affectation de l'encadrant, déclaration du stage, convention, émission et signature, rapport final, tableau de bord, soutenance. Sans eux, le processus reste manuel.
- **Should (3)** : livrables intermédiaires (US-17, US-18) et correction du rapport final par l'encadrant (US-19).
- **Could (3)** : module d'offres partenaires (US-20 à US-22).
- La colonne TO-BE renvoie au schéma : 1 Déclaration et validation du stage · 2 Convention, validation, signature · 3 Suivi, livrables et rapport · 4 Finalisation et soutenance · 5 Offres partenaires.
- Les priorités seront alignées sur la matrice MoSCoW du groupe, en cours de discussion.

## Must : MVP (17 stories, dont US-23 ajoutée le 2026-10-12)

| ID | TO-BE | User story | Critères d'acceptation |
| --- | --- | --- | --- |
| US-01 | 1 | En tant qu'**étudiant**, je veux déclarer mon stage trouvé par mes propres moyens en remplissant ma fiche de stage en ligne, afin de ne plus passer par des formulaires et échanges dispersés. | Identité pré-remplie ; origine du stage (réseau, site d'emploi, offre partenaire) ; brouillon possible ; envoi bloqué si champ obligatoire vide. |
| US-02 | 1 | En tant qu'**encadrant**, je veux être notifié et vérifier la conformité de la fiche de stage, afin de garantir que le sujet correspond au cursus. | Notification à l'envoi de la fiche ; motif obligatoire si refus ; l'étudiant corrige sa fiche et la renvoie. |
| US-03 | 1 | En tant qu'**étudiant**, je veux que la convention PDF soit générée à partir de ma fiche validée, afin de ne pas ressaisir les informations. | Toutes les données de la fiche reprises ; numéro unique ; PDF téléchargeable ; génération possible seulement si fiche conforme. |
| US-04 | 2 | *(réécrite le 2026-10-12, à valider)* En tant qu'**agent du Service Stages**, je veux contrôler la convention générée et l'émettre signée par le directeur des études, afin de la transmettre en quelques minutes au lieu de plusieurs jours. | Contrôle possible avec retour motivé à l'étudiant ; signature de l'école apposée ; historique horodaté ; étudiant et entreprise notifiés. *Ancienne version : validation Encadrant > Service Stages > Responsable (abandonnée).* |
| US-05 | 2 | En tant que **signataire (école, entreprise, étudiant)**, je veux signer la convention en ligne, afin de supprimer les signatures papier. | L'école (directeur des études) signe d'abord, puis l'entreprise et l'étudiant ; convention verrouillée ; signatures horodatées ; archivage. |
| US-06 | 2 | En tant qu'**agent du Service Stages**, je veux que la plateforme relance les validateurs et signataires en retard, afin de ne plus relancer à la main. | Délai paramétrable ; e-mail avec lien direct ; relances tracées ; arrêt dès l'action faite. |
| US-07 | 2 | En tant qu'**agent du Service Stages**, je veux exporter les conventions signées en CSV pour WebAurion, afin d'éviter la double saisie. | Conventions signées uniquement ; colonnes au format WebAurion ; fichier horodaté. |
| US-08 | 1 | En tant qu'**agent du Service Stages**, je veux importer les étudiants et encadrants depuis WebAurion (CSV), afin de ne pas créer les comptes à la main. | Rapport d'erreurs par ligne ; pas de doublons ; données utilisées pour pré-remplir la fiche. |
| US-09 | 3 | En tant qu'**étudiant**, je veux déposer mon rapport de stage final en ligne, afin d'avoir une preuve de dépôt sans e-mail. | PDF uniquement ; horodatage et accusé de réception ; dépôt bloqué après la date limite. |
| US-10 | 3 | En tant qu'**étudiant**, je veux recevoir des relances automatiques avant la date limite, afin de ne pas dépasser le délai. | Calendrier paramétrable ; arrêt dès le dépôt ; Service Stages informé des retards. |
| US-11 | 3 | En tant qu'**agent du Service Stages**, je veux consulter un tableau de bord des stages, afin de piloter sans relancer chaque personne. | Stages par étape ; conventions en attente ; rapports déposés et en retard ; mise à jour automatique. |
| US-12 | 4 | En tant que **membre du jury**, je veux indiquer mes disponibilités via un sondage en ligne, afin d'éviter les échanges de mails. | Sondage envoyé automatiquement ; créneaux à cocher ; rappel en cas de non-réponse. |
| US-13 | 4 | En tant qu'**agent du Service Stages**, je veux valider un planning de soutenances proposé automatiquement, afin d'éviter les conflits de salles et de jurys. | Un jury, une salle et un étudiant par créneau ; validation ou nouvelle proposition. |
| US-14 | 4 | En tant qu'**étudiant ou membre du jury**, je veux recevoir ma convocation automatiquement, afin de connaître date, heure et salle sans relance. | E-mail dès la validation du planning ; mis à jour si le planning change. |
| US-15 | 4 | En tant que **membre du jury**, je veux saisir le PV et la note en ligne, afin d'éviter les documents papier. | PV pré-rempli ; note obligatoire ; validation par le Service Stages ; PV rattaché au dossier. |
| US-16 | 4 | En tant qu'**agent du Service Stages**, je veux exporter les notes validées vers WebAurion et archiver le dossier, afin de clôturer sans ressaisie. | Notes validées uniquement ; format CSV WebAurion ; dossier archivé (convention, rapport, PV). |
| US-23 | 1 | *(ajoutée le 2026-10-12)* En tant qu'**agent du Service Stages**, je veux affecter un encadrant à chaque étudiant, afin que l'étudiant sache à qui soumettre son stage. | Un encadrant par étudiant et par stage ; encadrant et étudiant notifiés ; affectation modifiable et historisée ; liste des étudiants sans encadrant. |

## Should (3 stories)

| ID | TO-BE | User story | Critères d'acceptation |
| --- | --- | --- | --- |
| US-17 | 3 | En tant qu'**étudiant**, je veux déposer mes livrables intermédiaires en ligne, afin d'avoir une trace de chaque remise pendant le stage. | Liste des livrables avec date limite ; dépôt PDF horodaté ; statut visible (à déposer, déposé, validé, à corriger). |
| US-18 | 3 | En tant qu'**encadrant**, je veux valider ou demander la correction d'un livrable, afin de suivre l'avancement sans échanges de mails. | Décision avec commentaire ; étudiant notifié ; relance automatique avant chaque date limite. |
| US-19 | 3 | En tant qu'**encadrant**, je veux corriger le rapport final et saisir mon évaluation en ligne, afin de centraliser la correction et la note dans le dossier. | Commentaires sur le rapport ; évaluation enregistrée ; visible du Service Stages ; alimente la note de soutenance. |

## Could : module optionnel d'offres partenaires (3 stories)

| ID | TO-BE | User story | Critères d'acceptation |
| --- | --- | --- | --- |
| US-20 | 5 | En tant qu'**entreprise partenaire**, je veux proposer une offre de stage via un formulaire public, afin de la diffuser aux étudiants sans inscription. | Accès par lien sans authentification ; champs obligatoires ; e-mail de confirmation ; statut « en modération ». |
| US-21 | 5 | En tant qu'**agent du Service Stages**, je veux modérer les offres reçues (publier ou refuser), afin de n'afficher que des offres conformes. | Motif obligatoire si refus ; entreprise notifiée dans les deux cas. |
| US-22 | 5 | En tant qu'**étudiant**, je veux consulter les offres des entreprises partenaires, afin de les comparer à mes autres pistes. | Seules les offres publiées ; filtres type, domaine, durée, lieu ; une offre choisie pré-remplit la fiche de stage. |
