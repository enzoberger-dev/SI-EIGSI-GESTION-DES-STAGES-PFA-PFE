# Proposition de schéma de base de données corrigé

Cette proposition répond aux problèmes repérés dans le modèle du rapport de conception et intègre les décisions communiquées. Elle décrit les tables, leurs rôles et leurs relations en langage simple. Ce n’est pas encore un script SQL prêt à exécuter.

## 1. Comptes, entreprises et stages

### `UTILISATEUR`

- **Clé primaire :** `id_utilisateur`.
- Informations de compte : nom, prénom, e-mail et rôle.
- L’e-mail est obligatoire et unique.
- Les rôles autorisés comprennent étudiant, encadrant, agent du Service Stages, responsable et juré.

### `ENTREPRISE`

- **Clé primaire :** `id_entreprise`.
- Raison sociale, adresse et coordonnées du contact.
- L’entreprise n’a pas nécessairement de compte : elle peut recevoir un lien sécurisé par e-mail.

### `STAGE`

- **Clé primaire :** `id_stage`.
- **Clés étrangères :** `id_etudiant` et `id_encadrant` vers `UTILISATEUR`, `id_entreprise` vers `ENTREPRISE`, et éventuellement `id_offre` vers `OFFRE`.
- Contient le type de stage (PFA ou PFE), le sujet, la description, les dates, l’origine, le nom du tuteur d’entreprise et l’état du dossier.
- Règles : la date de fin doit être après la date de début ; une offre n’est liée au stage que si son origine est « offre partenaire ».

### `OFFRE`

- **Clé primaire :** `id_offre`.
- **Clé étrangère :** `id_entreprise` vers `ENTREPRISE`.
- Contient le type, la description, le lieu, la durée, le statut, les dates de dépôt et de modération, ainsi que le motif en cas de refus.
- Le motif de refus est obligatoire quand le statut est « refusée ».
- Une offre peut être liée à plusieurs stages ; chaque stage est lié à zéro ou une offre.

### `CANDIDATURE`

- **Clé primaire :** `id_candidature`.
- **Clés étrangères :** `id_offre` vers `OFFRE`, `id_etudiant` vers `UTILISATEUR` et, après acceptation, `id_stage` vers `STAGE`.
- Contient la date de candidature, le statut et, si besoin, un message de l’étudiant.
- Une candidature acceptée peut être associée au stage créé pour cette offre et cet étudiant. `id_stage` est facultatif et unique : un stage provient au maximum d’une candidature.
- La règle proposée est une candidature au maximum par étudiant et par offre.

## 2. Convention, validations et signatures

### `CONVENTION`

- **Clé primaire :** `id_convention`.
- **Clé étrangère unique :** `id_stage` vers `STAGE` — une convention au maximum par stage.
- Contient le numéro unique, le statut et la référence du PDF généré.
- Un stage peut ne pas encore avoir de convention.

### `VALIDATION_CONVENTION`

- **Clé primaire :** `id_validation`.
- **Clés étrangères :** `id_convention` vers `CONVENTION` et `id_validateur` vers `UTILISATEUR`.
- Contient le niveau (encadrant, Service Stages, responsable), la décision, le commentaire et la date.
- Une convention ne peut avoir qu’une validation par niveau. Un refus exige un commentaire.
- Les validations respectent l’ordre défini par le processus.

### `SIGNATURE_CONVENTION`

- **Clé primaire :** `id_signature`.
- **Clé étrangère :** `id_convention` vers `CONVENTION`.
- Contient le type de signataire (étudiant, entreprise ou école), la date, l’empreinte du document et, pour l’entreprise, son adresse de contact.
- Une convention ne peut avoir qu’une signature par type de signataire.

## 3. Livrables, rapport et évaluations

### `LIVRABLE`

- **Clé primaire :** `id_livrable`.
- **Clé étrangère :** `id_stage` vers `STAGE`.
- Décrit le livrable attendu et sa date limite.

### `DEPOT_LIVRABLE`

- **Clé primaire :** `id_depot`.
- **Clé étrangère :** `id_livrable` vers `LIVRABLE`.
- Une ligne correspond à une tentative de dépôt : référence du fichier, date, statut et commentaire de retour.
- Plusieurs tentatives sont autorisées pour garder l’historique des demandes de correction et des redépôts.

### `DEPOT_RAPPORT_FINAL`

- **Clé primaire :** `id_depot_rapport`.
- **Clé étrangère :** `id_stage` vers `STAGE`.
- Une ligne représente un dépôt distinct et contient le fichier, la date, le statut (déposé, à corriger ou corrigé) et le commentaire de retour.
- Les redépôts sont de nouvelles lignes ; l’historique n’est jamais écrasé. La date limite peut être portée par une table séparée de consigne de dépôt ou répétée par dépôt selon l’implémentation.

### `EVALUATION_RAPPORT`

- **Clé primaire :** `id_evaluation`.
- **Clés étrangères :** vers le dépôt évalué dans `DEPOT_RAPPORT_FINAL` et vers l’encadrant évaluateur de l’école dans `UTILISATEUR`.
- Contient les commentaires, les résultats de l’évaluation et la date.
- L’évaluation par le tuteur d’entreprise n’est pas incluse dans le MVP ; seul son nom est conservé dans la fiche de stage.

## 4. Disponibilités, planning et soutenances

### `CAMPAGNE_SOUTENANCE`

- **Clé primaire :** `id_campagne`.
- Représente une période de préparation et de planification des soutenances.

### `DISPONIBILITE`

- **Clé primaire :** `id_disponibilite`.
- **Clés étrangères :** vers `CAMPAGNE_SOUTENANCE` et vers le juré dans `UTILISATEUR`.
- Contient l’heure de début et l’heure de fin d’un créneau disponible.

### `SOUTENANCE`

- **Clé primaire :** `id_soutenance`.
- **Clés étrangères :** vers `STAGE` et vers `CAMPAGNE_SOUTENANCE`.
- La clé étrangère vers `STAGE` est unique : un stage a au maximum une soutenance et il n’y a pas de rattrapage dans le MVP.
- Contient la date et l’heure, la salle, la note saisie par le jury, le texte structuré du procès-verbal (PV), son statut de validation, la clé étrangère vers le validateur du Service Stages dans `UTILISATEUR` et la date de validation.
- Le PV est saisi dans le formulaire en ligne ; aucun fichier de PV n’est archivé pour le MVP.
- La note, si elle est saisie, doit être comprise entre 0 et 20.
- La soutenance peut ne pas encore être planifiée pour un stage.

### `JURY_SOUTENANCE`

- **Clés étrangères :** `id_soutenance` vers `SOUTENANCE` et `id_jure` vers `UTILISATEUR`.
- **Clé primaire composée :** `id_soutenance` + `id_jure`.
- Cette association permet à plusieurs jurés de participer à une soutenance et empêche d’ajouter deux fois le même juré à cette soutenance.

Le système de planning doit également vérifier qu’un même juré ou une même salle n’est pas réservé pour deux soutenances qui se chevauchent.

## 5. Notifications, imports et exports

### `NOTIFICATION`

- **Clé primaire :** `id_notification`.
- **Clé étrangère :** vers le destinataire dans `UTILISATEUR`, lorsque celui-ci possède un compte.
- Contient le type de notification, l’adresse utilisée, la date prévue, la date d’envoi, le résultat et le lien vers le dossier concerné.
- Permet de garder une trace des rappels, convocations et échecs d’envoi. Pour une entreprise sans compte, l’adresse e-mail sert de destinataire.

### `IMPORT_LOT`

- **Clé primaire :** `id_import`.
- Contient le fichier importé, la date, l’utilisateur qui a lancé l’import et son état général.

### `ERREUR_IMPORT`

- **Clé primaire :** `id_erreur`.
- **Clé étrangère :** `id_import` vers `IMPORT_LOT`.
- Contient le numéro de ligne du CSV et l’explication de l’erreur, pour rendre le rapport d’import demandé par le backlog.

L’historique des exports WebAurion peut être ajouté si l’école doit retrouver les fichiers transmis. Sinon, les CSV peuvent être générés à la demande sans table d’historique.

## 6. Relations principales

- Un étudiant peut déclarer plusieurs stages ; chaque stage est rattaché à un étudiant, un encadrant et une entreprise.
- Un stage peut provenir d’au plus une offre, et une offre peut être associée à plusieurs stages.
- Un stage possède au plus une convention.
- Une convention possède plusieurs validations, à raison d’une par niveau, et jusqu’à trois signatures, une par type de signataire.
- Un stage possède plusieurs livrables, et chaque livrable peut avoir plusieurs tentatives de dépôt.
- Un stage peut avoir plusieurs dépôts de rapport final, évalués par l’encadrant ; chaque dépôt est conservé dans `DEPOT_RAPPORT_FINAL`.
- Une campagne regroupe les disponibilités des jurés et les soutenances planifiées.
- Une soutenance peut associer plusieurs jurés via `JURY_SOUTENANCE`.
- Un étudiant peut candidater à plusieurs offres et une offre peut recevoir plusieurs candidatures ; `CANDIDATURE` porte ces relations.
- Un import CSV possède plusieurs erreurs éventuelles.

## 7. Décisions intégrées

- Les étudiants peuvent candidater aux offres.
- L’évaluation du tuteur d’entreprise est exclue du MVP ; son nom est conservé dans la fiche de stage et l’évaluation est faite par l’encadrant de l’école.
- Le PV est un formulaire structuré (note et texte), rempli par le jury puis validé par le Service Stages ; aucun fichier de PV n’est conservé pour le MVP.
- Chaque dépôt du rapport final est enregistré séparément, avec sa date et son statut, afin de conserver l’historique.
- Une offre peut être liée à plusieurs stages ; chaque stage peut être lié à zéro ou une offre.
- Un stage possède au maximum une convention et une soutenance ; aucune soutenance de rattrapage n’est prévue dans le MVP.

Le tableau de bord peut être calculé à partir des étapes, statuts et dates du dossier ; une table séparée n’est pas nécessaire tant que ses indicateurs restent calculables de cette manière.
