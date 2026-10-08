# MVP réaliste pour un débutant avec une IA

## 1. Classement des fonctionnalités

### Indispensables (à garder dans le MVP)

1. Connexion et rôles (étudiant, encadrant, Service Stages, responsable).
2. Déclaration du stage par l’étudiant.
3. Validation ou refus de la fiche par l’encadrant avec motif.
4. Publication d’offres par le Service Stages et candidature des étudiants.
5. Génération de la convention PDF et validation par les 3 niveaux.
6. Dépôt du rapport final, historique des dépôts et évaluation par l’encadrant.

Le point important : on garde 5 fonctionnalités de bout en bout, et on évite les fonctions d’assemblage ou de pilotage avancé. Les 6e point ci-dessus est bien plus large qu’il n’y paraît ; il couvre au moins un flux complet : soumettre, vérifier, corriger, évaluer.

### Utiles mais à faire après le MVP

- Tableau de bord du responsable.
- Rappels e-mail automatiques.
- Livrables intermédiaires et corrections avant le rapport final.
- Import/Export CSV WebAurion.
- Signature électronique.
- Planification des soutenances, disponibilité du jury et PV en ligne.
- Espace de modération des offres pour les entreprises.

### À faire plus tard

- Formulaire public pour les entreprises.
- Module d’offres côté entreprise complet.
- Statistiques de suivi et analyses avancées.
- Intégration au système de l’école ou WebAurion.
- Messagerie interne et approbation multicritère.

## 2. MVP retenu : 5 fonctionnalités de bout en bout

### Fonction 1 — Authentification et rôles

Objectif : chaque profil voit uniquement ses écrans et actions.

- Étudiant : déclaration du stage, candidature, dépôt du rapport.
- Encadrant : validation du stage, demande de correction, évaluation du rapport.
- Service Stages : publication des offres, validation de la convention, suivi des dossiers.
- Responsable : validation finale de la convention, vue globale.

Étapes simples :
1. Créer les comptes test.
2. Ajouter des rôles.
3. Vérifier l’accès par page.
4. Tester des cas refusés.

### Fonction 2 — Déclaration du stage

Objectif : l’étudiant remplit sa fiche de stage et l’encadrant la valide.

Étapes simples :
1. Formulaire : type de stage, entreprise, sujet, dates, origine, nom du tuteur.
2. Enregistrement en brouillon.
3. Soumission.
4. Notification de l’encadrant.
5. Validation ou refus avec motif.
6. Retour à l’étudiant.

### Fonction 3 — Candidatures aux offres

Objectif : les offres sont publiées et les étudiants peuvent candidater.

Étapes simples :
1. Le Service Stages crée une offre.
2. L’étudiant voit les offres publiées.
3. L’étudiant envoie une candidature.
4. Le statut passe en « postulée » puis « retenue / refusée ».
5. Si l’offre est retenue, le stage est créé ou associé au dossier.

### Fonction 4 — Convention PDF + validations

Objectif : générer une convention à partir du stage validé, puis la faire valider à 3 niveaux.

Étapes simples :
1. Générer le PDF à partir des données du stage.
2. Vérifier que la convention n’est générée que si le stage est conforme.
3. L’encadrant valide ou refuse.
4. Le Service Stages valide ou refuse.
5. Le responsable valide ou refuse.
6. Conserver l’historique des décisions.

### Fonction 5 — Rapport final avec historique

Objectif : l’étudiant dépose son rapport et l’encadrant le valide ou le corrige.

Étapes simples :
1. L’étudiant choisit le fichier PDF.
2. Le dépôt est enregistré dans une ligne distincte.
3. Le statut est « déposé ».
4. L’encadrant peut demander une correction ou donner une évaluation.
5. Le statut devient « à corriger » ou « corrigé ».
6. L’historique reste visible.

## 3. Ordre réaliste de développement

### Étape 1 — Base + authentification

- Créer la base de données.
- Créer la table `UTILISATEUR`.
- Ajouter la connexion.
- Ajouter les rôles.

### Étape 2 — Stage + validation.

- `STAGE`, `ENTREPRISE`, `OFFRE` et `CANDIDATURE`.
- Écran d’ajout de stage.
- Validation de l’encadrant.

### Étape 3 — Convention.

- `CONVENTION` et `VALIDATION_CONVENTION`.
- Génération PDF.
- Trois niveaux de validation.

### Étape 4 — Rapport final.

- `DEPOT_RAPPORT_FINAL`.
- Évaluation par l’encadrant.
- Historique des dépôts.

### Étape 5 — Vérification fonctionnelle.

- Tester chaque rôle.
- Vérifier les cas limites.
- Corriger les erreurs de flux.

## 4. Vérification de la stack technique

### Stack proposée dans les documents

- Frontend : React + Vite + Tailwind
- Backend : Node.js + Express
- Base de données : PostgreSQL
- Authentification : JWT
- PDF : génération côté backend

### Est-ce que cette pile est adaptée ?

Oui, mais elle est un peu lourde pour un débutant qui veut apprendre sans se perdre. Le vrai risque est la multiplication des technologies : interface, API, base, JWT, génération PDF, et éventuellement Docker.

### Alternative plus simple et plus réaliste

Pour le MVP, je recommande :

- Frontend : HTML + CSS simple, ou un petit app front en JavaScript sans framework.
- Backend : Node.js + Express.
- Base de données : SQLite au lieu de PostgreSQL.
- Authentification : sessions côté serveur, plus simples à comprendre.
- PDF : génération côté backend avec bibliothèque légère.

Pourquoi c’est mieux ?

- Moins de dépendances.
- Moins d’erreurs de configuration.
- Plus facile à déboguer.
- L’IA peut t’aider plus facilement à construire le code pas à pas.
- Tu gardes le même langage JavaScript sur tout le projet.

### Conclusion

Le MVP le plus raisonnable pour un débutant est :

- compte et rôles,
- déclaration du stage,
- candidatures aux offres,
- convention et validation,
- rapport final avec historique.

Tout le reste est mieux placé dans une phase 2.
