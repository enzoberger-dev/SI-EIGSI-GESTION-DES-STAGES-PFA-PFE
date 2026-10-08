# Gestion des stages PFA/PFE

Application web de gestion des stages PFA/PFE de l’EIGSI Casablanca.

## Installer et lancer l’application (Windows)

### Prérequis

- Node.js 22 ou une version plus récente.
- PowerShell ouvert dans le dossier du projet.

### Première installation

Depuis le dossier du projet, exécute les commandes suivantes :

```powershell
npm install
npm run users:demo
$env:PORT = "3000"
npm start
```

La première commande télécharge les dépendances. La commande `users:demo` crée automatiquement la base SQLite et ses données d’exemple, puis attribue un mot de passe temporaire aléatoire à chaque compte de démonstration qui n’en possède pas encore.

Sur une installation de npm qui bloque les scripts natifs, si `npm install` indique que le script de `better-sqlite3` a été bloqué, autorise uniquement ce script puis relance la création des comptes :

```powershell
npm install-scripts approve better-sqlite3
npm run users:demo
```

**Copie les mots de passe affichés dans le terminal et garde-les en lieu sûr.** Pour protéger les comptes, ils ne seront pas réaffichés lors d’une prochaine exécution de `npm run users:demo`. Cette commande n’est pas nécessaire à chaque lancement.

Quand le terminal affiche `Application prête`, ouvre <http://localhost:3000>. Pour arrêter le serveur, retourne dans le terminal et appuie sur `Ctrl+C`.

### Lancements suivants

Dans le dossier du projet, il suffit de lancer :

```powershell
$env:PORT = "3000"
npm start
```

La base locale se trouve dans `data/stages.sqlite`. Ne supprime pas ce fichier pour relancer l’application : il contient les données locales et les mots de passe de démonstration.

## Bilan du MVP

### Fonctionnalités terminées

- Connexion, déconnexion et espaces séparés par rôle : étudiant, encadrant, Service Stages, responsable et compte d’entreprise partenaire.
- Affectation d’un encadrant, déclaration d’un stage en brouillon, soumission, refus motivé, correction et nouvelle validation.
- Publication d’offres par le Service Stages, candidatures étudiantes et décision de l’entreprise sur les offres qui lui appartiennent.
- Génération du PDF de convention après validation du stage, puis validations successives par l’encadrant, le Service Stages et le responsable.
- Dépôt du rapport final en PDF après la date de fin du stage, demande de correction, redépôt conservé dans l’historique et évaluation par l’encadrant.

### Fonctions laissées hors MVP

- Notifications automatiques par e-mail, conformément au périmètre retenu.
- Signature électronique, livrables intermédiaires, soutenances et procès-verbaux en ligne.
- Import/export et intégration à WebAurion, statistiques et tableau de bord avancé du responsable.
- Inscription publique des entreprises et modération avancée de leurs offres.

### Problème connu

Les données d’exemple contiennent un dépôt de rapport dont le chemin est `uploads/demo/rapport-pfa.pdf`, mais ce PDF n’est pas fourni. Cette entrée apparaît dans l’historique avec un fichier indisponible ; les autres dépôts PDF téléversés par l’application sont conservés dans un dossier privé.

Les deux stages fournis en exemple se terminent en 2027. Comme un nouveau rapport ne peut être déposé qu’après la date de fin, prépare un stage terminé avec un vrai PDF si tu veux montrer un dépôt pendant une démonstration.

## Structure du projet

- `src/server.js` : démarre l’application Express.
- `src/routes/` : routes et pages des fonctionnalités.
- `src/views/` : pages HTML partagées.
- `src/db/` : connexion, schéma, données de démonstration et migrations SQLite.
- `src/middleware/` : contrôle de connexion et des rôles.
- `public/` : feuilles de style et fichiers du navigateur.
- `uploads/` : documents privés déposés ou générés ; ne pas y stocker de secrets.
- `docs/` : documentation et journal du projet.

## Informations de sécurité

Cette configuration sert aux essais locaux uniquement. Le stockage des sessions en mémoire et la clé de session de développement ne conviennent pas à une mise en production. Les mots de passe aléatoires sont affichés une seule fois : garde-les en lieu sûr et ne les partage pas.
