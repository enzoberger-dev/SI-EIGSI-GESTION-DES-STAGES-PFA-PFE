# 07 — MVP démo (GitHub Copilot, séance 3)

Retour : [[Accueil]]

> **Statut : prototype jetable.** Il a été fait pour le rendu de la séance 3 avec l'agent GitHub Copilot en mode Auto. La vraie version sera refaite avec Claude Code en s'appuyant sur la conception ([[05-Donnees-MCD]], [[03-Besoins-et-backlog]]). Cette démo sert à garder en tête **ce qu'on vise**, et d'inspiration.

## Où est-il
- Dépôt GitHub : sous-dossier `mvp_SAADALI_WALID/` (branche `main`) : `src/`, `public/`, `docs/`, `uploads/`, `_sauvegardes/`, `.github/`, `package.json`, `README.md`.
- Documents produits par l'agent dans `docs/` : `00-resume-projet.md`, `01-schema-corrige.md`, `02-mvp.md`, `journal.md`.
- Vidéo de démonstration : `SAADALI_Walid.mp4` (3 min 24, sous-titrée en français), à déposer dans le dossier `demo/` à la racine du dépôt (le dépôt montre un dossier `Demo/` le 12/10 : vérifier s'il contient bien la vidéo).

## Stack de la démo
Node.js 22 + Express, pages HTML, SQLite (`better-sqlite3`), sessions côté serveur (pas de JWT), PDFKit (convention), Multer (rapport PDF, 10 Mo max). Lancement : `npm install`, `npm run users:demo` (crée les comptes de démo avec des mots de passe aléatoires affichés une seule fois), puis `npm start` (variable `PORT`).

## Ce que la démo sait faire (5 parcours)
1. **Connexion et rôles** : étudiant, encadrant, Service Stages, responsable, compte entreprise (table dédiée `COMPTE_ENTREPRISE`).
2. **Déclaration du stage** : le Service Stages attribue un encadrant ; l'étudiant enregistre un brouillon, soumet ; l'encadrant accepte ou refuse avec motif obligatoire ; correction et renvoi ; historique des décisions.
3. **Offres et candidatures** : le Service Stages publie des offres ; l'étudiant candidate (message facultatif, une fois par offre) ; l'entreprise retient ou refuse ; la candidature retenue se relie au stage. *(Walid a voulu garder la candidature : « facultatif ne veut pas dire que les élèves ne peuvent pas candidater ».)*
4. **Convention** : PDF généré seulement si le stage est conforme ; validations successives Encadrant → Service Stages → Responsable ; refus motivé = retour à l'étudiant puis nouveau cycle et nouvelle version du PDF ; anciens PDF et décisions conservés.
5. **Rapport final** : dépôt PDF possible à partir de la date de fin du stage ; demande de correction ou évaluation (commentaire + note facultative sur 20) par l'encadrant ; chaque redépôt crée une nouvelle ligne d'historique.

## Hors périmètre de la démo
Tableau de bord du responsable (écran indicatif), rappels e-mail, signature électronique, livrables intermédiaires, soutenances et PV, import/export WebAurion, statistiques, inscription publique des entreprises, notifications automatiques.

## Comptes de démonstration (fictifs)
Adam El Amrani (`adam.elamrani@example.test`, étudiant), Yasmine Benali (`yasmine.benali@example.test`, étudiante), Sara Bennani (encadrante), Nadia Alaoui (`nadia.alaoui@example.test`, Service Stages), Karim Idrissi (`karim.idrissi@example.test`, responsable), Nora Mansouri (`nora.mansouri@atlas-energies.example.test`, entreprise Atlas Energies). Les mots de passe ne sont **pas** dans ce vault.

## Bugs et limites connus
- Le dépôt de rapport ne peut pas être démontré : le PDF d'exemple `uploads/demo/rapport-pfa.pdf` n'existe pas, son entrée d'historique est datée avant la fin du stage, et les stages d'exemple finissent en 2027 (l'application bloque donc les nouveaux dépôts, ce qui est voulu). Il faudrait un stage terminé et un vrai PDF dans les données d'exemple.
- Après validation par le Service Stages, l'écran « Suivre ma convention » affiche toujours « En cours de validation » : **c'est normal**, il reste la validation du responsable (3e niveau) ; seul un parcours complet passe le statut à « validée ».
- Pas de tests automatisés ; vérifications manuelles décrites dans le journal.
- Mots de passe temporaires et clé de session de développement : usage local uniquement.

## Ce qui a bien fonctionné (à reprendre)
- Méthode « plan puis OK », sauvegardes dans `_sauvegardes/`, journal tenu à jour.
- Séparation par rôle avec contrôle d'accès sur chaque route.
- Historique conservé (validations par cycle, dépôts de rapport) au lieu d'écraser.
- Convention en PDF avec numéro unique et téléchargement protégé.
