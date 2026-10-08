# Journal de travail

## 2026-10-05

- **Fait :** Création de `.github/copilot-instructions.md` avec la description du projet, la stack choisie, la structure des dossiers, les règles de travail et les liens vers les documents de référence.
- **Fait :** Création de ce journal avec l’accord de l’utilisateur.
- **Fait :** Initialisation du projet Node.js/Express avec les dépendances de sessions et SQLite, une route de test « Hello », un README de démarrage et une sauvegarde du README d’origine.
- **Vérification :** `npm audit --omit=dev` ne signale aucune vulnérabilité ; `http://localhost:3000` répond avec HTTP 200 et le texte « Hello ».
- **Fait :** Création du schéma SQLite (`src/db/schema.sql`), des données fictives réutilisables (`src/db/seed.sql`), chargés par le connecteur existant. Ajout d’une route de démonstration des stages et sauvegarde des fichiers de connexion et serveur avant modification.
- **Vérification :** 19 tables créées, intégrité SQLite correcte, aucune clé étrangère invalide ; 6 utilisateurs, 2 stages et 2 candidatures affichés ; les insertions de test ne créent pas de doublons. `/api/demo-data` répond HTTP 200 avec les stages exemples.
- **Fait :** Ajout de la connexion par e-mail et mot de passe haché, des sessions, de la déconnexion et des espaces protégés pour les quatre rôles MVP. Création d’une commande locale qui attribue des mots de passe temporaires aléatoires aux comptes de démonstration ; l’API de démonstration est réservée au Service Stages et au responsable.
- **Vérification :** Connexion et déconnexion testées pour les quatre rôles ; mauvais mot de passe refusé ; accès croisé aux rôles refusé (HTTP 403) ; API anonyme redirigée vers la connexion ; formulaire et espace étudiant vérifiés dans le navigateur. Dix fichiers JavaScript passent `node --check` et `npm audit --omit=dev` ne détecte aucune vulnérabilité.
- **À faire :** Remplacer les mots de passe temporaires avant tout usage réel, puis implémenter les fonctions métier des écrans du MVP par étapes approuvées.

## Déclaration et validation d’un stage — 2026-10-05

- **Fait :** Le Service Stages peut attribuer un encadrant avant la déclaration. L’étudiant peut enregistrer un brouillon incomplet, soumettre sa fiche et, si elle est refusée, la corriger puis la renvoyer. L’encadrant voit les fiches qui lui sont attribuées, peut les accepter ou les refuser avec un motif obligatoire. Chaque décision est conservée dans l’historique.
- **Fait :** Ajout des tables d’affectation, de brouillon et d’historique de validation, des écrans et routes correspondants ainsi que de leurs styles. Le bouton de brouillon ignore la validation obligatoire du navigateur pour permettre une sauvegarde partielle.
- **Vérification :** Parcours complet exécuté en HTTP sur une copie temporaire de la base : affectation, brouillon partiel, soumission, refus sans motif bloqué, refus motivé, correction, renvoi puis acceptation. Deux décisions restent dans l’historique et `PRAGMA foreign_key_check` ne signale aucune erreur. La syntaxe des 11 fichiers JavaScript et les diagnostics VS Code sont corrects. L’application démarre et la page de connexion s’ouvre à `http://localhost:3003`.
- **À faire :** Les notifications automatiques de l’encadrant et les tests manuels avec clics pour chacun des rôles ne sont pas inclus dans cette étape.
