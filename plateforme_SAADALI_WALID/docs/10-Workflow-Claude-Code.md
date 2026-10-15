# 10 — Travailler avec Claude Code

Retour : [[Accueil]]

## Mise en place
- Ouvrir **ce dossier** (`PROJETGestionStage`) comme dossier de travail (dans VS Code : *Fichier > Ouvrir le dossier*, ou dans l'application de bureau Claude). Si l'agent liste tout le dossier personnel au lieu du projet, c'est que le dossier n'est pas ouvert : le rouvrir, relancer une session.
- Se connecter avec son compte Claude. Se déconnecter : commande `/logout`.
- Choisir le mode de permission : **Manuel** ou **Plan** pour valider avant les modifications (comme la règle du prof : plan puis « OK »).
- `CLAUDE.md` est lu automatiquement à chaque session ; il remplace le fichier `.github/copilot-instructions.md` de la démo.

## Rituel d'une session
1. « Nouvelle session : relis `CLAUDE.md`, `docs/08-Decisions-ouvertes.md`, `docs/09-Prochaines-etapes.md` et `journal/journal.md`. Fais un point en 10 lignes, puis propose la prochaine étape. »
2. Demander un **plan court** pour une fonctionnalité (fichiers, étapes, test dans le navigateur). Répondre « OK » seulement si le plan est compris.
3. Après réalisation : tester, puis mise à jour du journal.
4. Si l'agent dérive : « Stop. Relis les instructions et résume où nous en sommes. Propose UNE seule prochaine étape. »
5. Si quelque chose casse : relire le journal et `_sauvegardes/` avant tout retour en arrière ; rien n'est supprimé sans accord.

## Prompts de départ utiles (adaptés de ceux du prof)
- Relire la conception : « Lis tous les fichiers de `docs/` et `reference/`. Donne les incohérences entre le backlog, les écrans et la base, et au plus 5 questions. Ne modifie rien. »
- Construire une fonctionnalité : « Je veux construire [US-xx]. Relis `docs/03-Besoins-et-backlog.md` et `docs/05-Donnees-MCD.md`. Propose un plan numéroté ; n'écris pas de code avant mon OK. »
- Comprendre le code : « Explique-moi le fichier [nom] comme si je n'avais jamais codé. »

## Outils avancés à envisager (Walid veut qu'on les lui explique, pas qu'on les écarte)
Agents spécialisés, skills, serveurs MCP, tests automatisés, Docker : à proposer au bon moment avec avantages et coût de mise en place, puis laisser Walid choisir.

## Organisation du dossier et de Git (décidée le 2026-10-12)
- Le code vit dans **`app/`**, à côté des notes. Obsidian n'affiche que les `.md` : le code s'ouvre dans VS Code ou Claude Code. Dans Obsidian, exclure `app/` (réglage « Fichiers exclus » : à vérifier dans la version installée) pour éviter les ralentissements dus aux dépendances.
- ~~Un dépôt Git personnel~~ *(corrigé le 2026-10-12 : c'est un projet de groupe)*. **Pour l'instant, travail en local** dans ce dossier. Conseillé dès maintenant : `git init` (100 % local, rien n'est publié) pour garder un historique et pouvoir revenir en arrière.
- **Conseil de Claude pour plus tard** : un dépôt **dédié à l'application**, **privé**, dans une **organisation GitHub** du groupe (personne n'en est propriétaire seul, et on peut le transférer à l'école pour la mise en ligne). Le dépôt d'Enzo (public) reste pour les rendus du cours. On le déconseille pour l'application : il est public, mélange rendus, démos et `.zip`, et n'a qu'un administrateur.
- **Méthode à 4 (« GitHub Flow »)** quand le dépôt sera partagé : `main` toujours fonctionnel et jamais modifié directement ; une branche par lot (`feature/fiche-de-stage`), une personne par lot ; une pull request relue par un autre membre avant fusion ; des messages de commit clairs (`feat(stage): ...`, `fix(...)`, `docs(...)`).
- On **commit le code** (c'est le but de Git) ; on ne commit jamais secrets, bases de données, `uploads/` ni dépendances : le `.gitignore` à la racine s'en charge.
- Claude Code lit les fichiers dans le dossier local sans GitHub ; la connexion à GitHub ne sert qu'à pousser ou à gérer des demandes de fusion.
- Créer le dépôt **avant** la première ligne de code pour pouvoir revenir en arrière.

## Hygiène
- Pas de clés API, de mots de passe réels, de `.env` ni de bases de données dans le dépôt GitHub.
- Utiliser un compte de démo fictif ; les mots de passe de démo sont régénérés par script, jamais écrits dans les notes.
- Le vault peut être ouvert dans **Obsidian** (*Ouvrir un dossier comme coffre*) pour naviguer entre les notes grâce aux liens `[[...]]`.
