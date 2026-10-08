# Instructions Copilot — gestion des stages PFA/PFE

## Application

L’application centralise les dossiers de stages PFA et PFE de l’EIGSI Casablanca.
Les étudiants peuvent déclarer un stage et candidater aux offres publiées.
Les encadrants vérifient les stages et évaluent les rapports déposés.
Le Service Stages et le responsable valident les conventions générées en PDF.
Le MVP privilégie ces parcours essentiels avant les rappels, soutenances et intégrations avancées.

## Stack technique

- Frontend : HTML, CSS et JavaScript simples, sans framework pour le MVP.
- Backend : Node.js avec Express.
- Base de données : SQLite.
- Authentification : sessions côté serveur.
- Génération PDF : côté serveur avec une bibliothèque Node.js adaptée.
- La stack React/Vite, Tailwind, PostgreSQL et JWT est décrite dans les documents de conception comme proposition initiale ; pour le MVP débutant, suivre l’alternative plus simple retenue dans `docs/02-mvp.md`, sauf accord explicite contraire.

## Structure du dépôt

Structure actuelle :

- `README.md` : présentation générale.
- `docs/00-resume-projet.md` : résumé et inventaire du projet.
- `docs/01-schema-corrige.md` : proposition de modèle de données corrigé.
- `docs/02-mvp.md` : périmètre MVP et choix techniques.
- Les rapports PDF et les diagrammes BPMN restent des documents de référence à la racine.

Structure de code proposée lorsqu’elle sera approuvée :

- `src/server.js` : démarrage du serveur Express.
- `src/routes/` : routes de l’application.
- `src/views/` : pages HTML rendues par le serveur.
- `public/` : CSS, JavaScript navigateur et images.
- `src/db/` : accès à SQLite et initialisation du schéma.
- `src/middleware/` : vérification de session et de rôle.
- `uploads/` : fichiers déposés, si nécessaire ; ne pas y stocker de secrets.
- `docs/` : documentation du projet et journal de travail.

Ne crée pas cette structure de code avant que l’utilisateur ait approuvé le plan correspondant.

## Règles de travail

- Avant chaque étape de travail, proposer un plan court et attendre le « OK » de l’utilisateur avant de modifier des fichiers.
- Avancer par petites étapes et vérifier chaque étape avant de poursuivre.
- Ne jamais supprimer un fichier ni installer un outil ou une dépendance sans demander d’abord l’autorisation.
- Avant une modification importante d’un fichier existant, en faire une copie dans `_sauvegardes/` ; ne pas écraser une sauvegarde existante.
- Expliquer les erreurs et les choix techniques en français simple, adapté à une personne débutante.
- Écrire dans le code des commentaires clairs et utiles, notamment lorsque la logique n’est pas évidente ; éviter les commentaires qui répètent simplement le code.
- Après chaque étape réalisée et approuvée, mettre à jour `docs/journal.md` avec la date, ce qui a été fait et ce qui reste à faire. Si ce fichier n’existe pas, demander l’accord avant de le créer.
- Respecter les documents de conception et signaler les contradictions avant de choisir un comportement non confirmé.
- Garder les changements limités au besoin demandé et tester les fonctions touchées lorsque c’est possible.

## Documents de référence

- [Résumé du projet](../docs/00-resume-projet.md)
- [Schéma de données corrigé](../docs/01-schema-corrige.md)
- [Périmètre MVP](../docs/02-mvp.md)
