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

Les cinq parcours principaux retenus pour le MVP sont présents dans l’application :

- Connexion, déconnexion et espaces séparés par rôle : étudiant, encadrant, Service Stages, responsable et compte d’entreprise partenaire.
- Affectation d’un encadrant, déclaration d’un stage en brouillon, soumission, refus motivé, correction et nouvelle validation.
- Publication d’offres par le Service Stages, candidatures étudiantes et décision de l’entreprise sur les offres qui lui appartiennent.
- Génération du PDF de convention après validation du stage, puis validations successives par l’encadrant, le Service Stages et le responsable.
- Dépôt du rapport final en PDF après la date de fin du stage, demande de correction, redépôt conservé dans l’historique et évaluation par l’encadrant.

### Fonctionnalités restantes ou hors MVP

- L’écran de pilotage global du responsable est encore à construire ; son lien est un écran indicatif.
- Les fonctions prévues pour une phase ultérieure restent à faire : rappels par e-mail, signature électronique, livrables intermédiaires, soutenances et procès-verbaux en ligne.
- Import/export et intégration à WebAurion, statistiques avancées, inscription publique des entreprises et modération avancée de leurs offres.
- Les comptes de démonstration sont créés par une commande locale ; aucune inscription publique ni récupération de mot de passe n’est prévue dans le MVP.

### Bugs et limites connus

- Un rapport d’exemple pointe vers `uploads/demo/rapport-pfa.pdf`, mais ce fichier n’est pas fourni. Il apparaît dans l’historique comme indisponible.
- Ce rapport est daté du 4 octobre 2026 alors que le stage associé se termine le 31 janvier 2027. Cette incohérence concerne les données de démonstration : l’application bloque bien les nouveaux dépôts avant la date de fin.
- Les deux stages d’exemple se terminent en 2027. À la date du 8 octobre 2026, ils ne permettent donc pas de montrer un nouveau dépôt de rapport. Pour présenter le dépôt et la correction de bout en bout, prépare un stage de test terminé avec un véritable PDF.
- Il n’y a pas de script de tests automatisés dans `package.json` ; les parcours ont été vérifiés manuellement selon le journal du projet.

## Scénario de démonstration (3 minutes)

### À préparer avant la présentation

1. Lance l’application selon les commandes d’installation ci-dessus et exécute `npm run users:demo` une première fois. Garde les mots de passe temporaires affichés dans le terminal ; ils ne seront pas réaffichés ensuite.
2. Ouvre des onglets de navigateur déjà connectés avec les comptes de démonstration suivants : Adam (`adam.elamrani@example.test`), Nora de l’entreprise (`nora.mansouri@atlas-energies.example.test`), Nadia du Service Stages (`nadia.alaoui@example.test`), Karim responsable (`karim.idrissi@example.test`) et Yasmine (`yasmine.benali@example.test`). Utilise pour chacun le mot de passe obtenu lors de la préparation.
3. Ce parcours suppose une base d’exemple qui n’a pas déjà servi à cette démonstration. Les candidatures et validations faites pendant la présentation sont enregistrées durablement dans `data/stages.sqlite`.

| Temps | Étape |
| --- | --- |
| 0:00–0:30 | Avec Adam, ouvrir **Offres de stage**, consulter l’offre Atlas Energies et candidater. Montrer le message de confirmation. |
| 0:30–0:55 | Avec Nora, ouvrir **Candidatures reçues**, vérifier que la candidature d’Adam concerne son entreprise, puis la retenir. Préciser que la décision est conservée. |
| 0:55–1:15 | Avec Nadia, afficher **Gérer les offres** et montrer la publication des offres par le Service Stages. |
| 1:15–2:20 | Avec Nadia, ouvrir **Conventions** et valider le niveau Service Stages de la convention d’exemple. Avec Karim, valider le niveau responsable. Montrer l’historique des validations et le PDF. |
| 2:20–2:40 | Avec Yasmine, vérifier que la convention est maintenant validée et ouvrir son PDF depuis son espace. |
| 2:40–3:00 | Avec Adam, ouvrir **Rapport final** et montrer l’historique. Signaler honnêtement que l’entrée d’exemple n’a pas son PDF et que le dépôt d’un nouveau rapport attend la fin du stage. |

Pour une démonstration complète du rapport final, utilise un dossier de test dont la date de fin est passée et un vrai fichier PDF. Les mots de passe de démonstration sont destinés aux essais locaux uniquement.


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
