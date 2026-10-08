# Gestion des stages PFA/PFE

Application web de gestion des stages PFA/PFE de l’EIGSI Casablanca.

## Prérequis

- Node.js installé.

## Installer et lancer (Windows PowerShell)

Depuis le dossier du projet, lance ces commandes :

```powershell
npm install
$env:PORT = "3000"
npm start
```

Ouvre ensuite cette adresse dans ton navigateur : <http://localhost:3000>
La page de test affiche « Hello ».

Pour arrêter le serveur, retourne dans le terminal et appuie sur `Ctrl+C`.

## Structure

- `src/server.js` : démarre l’application Express.
- `src/routes/` : routes web.
- `src/views/` : pages HTML.
- `src/db/` : connexion à SQLite ; le fichier local est créé dans `data/`.
- `public/` : fichiers statiques du navigateur.
- `uploads/` : réservé aux futurs fichiers déposés ; son contenu n’est pas suivi par Git.
- `docs/` : documentation et journal du projet.

Les sessions utilisent le stockage mémoire temporaire d’Express pour le démarrage local. Ce stockage et la clé de session de développement ne conviennent pas à une mise en production.
