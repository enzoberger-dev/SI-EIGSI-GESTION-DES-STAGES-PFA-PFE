# 13 — Démonstration : installation et déroulé

> Pour la dernière séance : montrer la plateforme au prof, sur un autre PC (celui de Wael), sans rien préparer à la main.
> Lié à : [[12-Mise-en-ligne]], [[03-Besoins-et-backlog]], [[07-MVP-demo-Copilot]].

## 1. Installer la démo sur un PC (5 minutes, une seule fois)
1. **Python 3.10 ou plus récent** doit être installé. Sinon : <https://www.python.org/downloads/> et **cocher « Add python.exe to PATH »**. (Vérification : ouvrir une invite de commandes, taper `python --version`.)
2. Récupérer le dossier de la démo (archive `gestion-stages-demo.zip` sur clé USB ou Drive) et **extraire** le ZIP (clic droit → « Extraire tout »).
3. Dans le dossier extrait : **double-clic sur `LANCER_LA_DEMO.bat`**.
   - Premier lancement : 2 à 5 minutes (création de l'environnement, installation des outils, préparation des données). **Internet est nécessaire cette fois-là seulement.**
   - Le navigateur s'ouvre sur `http://localhost:8000/`. Ensuite, le lancement prend quelques secondes et fonctionne **sans Internet**.
4. Pour arrêter : fermer la fenêtre noire.

> **Conseil : faire le premier lancement la veille** (sur le PC de Wael) pour être sûr que tout marche et ne pas dépendre du Wi-Fi le jour J.

La démo utilise sa **propre base** (`demo.sqlite3`) et ses propres fichiers (`demo_uploads/`) : aucune vraie donnée n'est touchée. Pour repartir de zéro (après avoir validé des choses en direct) : **supprimer `demo.sqlite3`** puis relancer.

## 2. Les comptes
**Mot de passe de tous les comptes : `Demo-EIGSI-2026`** (comptes fictifs, valables seulement dans la base de démonstration).

| Compte (`…@example.test`) | Rôle | Situation |
|---|---|---|
| `nadia.alaoui` | Career Center | pilote tout (tableau de bord, conventions, soutenances, administration) |
| `adam.elamrani` | Étudiant 3e | convention signée, 1 livrable rendu |
| `imane.bouazza` | Étudiante 3e | fiche **soumise** : le coordinateur doit la valider |
| `hamza.tahiri` | Étudiant 3e | fiche en **brouillon** (incomplète) |
| `nour.benjelloun` | Étudiante 3e | **n'a pas encore déclaré** de stage |
| `yasmine.benali` | Étudiante 5e | convention **envoyée** : elle doit déposer le scan |
| `salma.cherkaoui` | Étudiante 5e | fiche **refusée** avec un motif |
| `reda.lamrani` | Étudiant 5e | stage **validé** : le Career Center doit générer la convention |
| `mehdi.ouazzani` | Étudiant 5e | soutenance passée : **PV à valider** |
| `kenza.alami` | Étudiante 5e | soutenance planifiée : le jury **saisit le PV** |
| `karim.idrissi` | Coordinateur 3e | valide les fiches de la 3e année |
| `sara.bennani` | Encadrante et jury | valide les fiches de la 5e, saisit les PV |
| `omar.tazi` | Encadrant et jury | |

> **Astuce** pour changer de compte vite : ouvrir une **fenêtre de navigation privée** pour le deuxième compte (les deux sessions restent séparées).

## 3. Déroulé de 7 à 8 minutes : « du stage à la soutenance »
Fil rouge : *avant, tout passait par des e-mails et des saisies à la main ; maintenant chacun voit où en est le dossier et ce qu'il doit faire.*

1. **Le Career Center d'abord (45 s)** — `nadia.alaoui`. Le **tableau de bord** montre en un coup d'œil ce qui attend : 1 fiche soumise, 1 stage à mettre en convention, 1 convention en signature, 1 PV à valider, et les étudiants par étape.
2. **Un étudiant (1 min)** — `adam.elamrani` → **Mon stage** : la **frise** (où j'en suis), la bannière « prochaine action », l'historique, les livrables. Montrer **« À propos et aide »** : il ne voit que ce qui concerne son rôle. Puis `hamza.tahiri` : la fiche incomplète liste ce qu'il manque avant de pouvoir soumettre.
3. **La validation (1 min)** — `karim.idrissi` → **Stages à valider** → *Imane* → **Valider** (montrer qu'un **refus exige un motif**). Retour sur `imane.bouazza` : la frise a avancé et elle a reçu un e-mail.
4. **La convention (1 min 30)** — `nadia.alaoui` → **Conventions** : générer la convention de **Reda** (PDF automatique), l'envoyer. Puis `yasmine.benali` : télécharger la convention, **déposer le scan** (fichier prêt : `exemples/scan_convention_exemple.pdf`). Retour Career Center : **valider la signature** → les livrables se créent tout seuls.
5. **La soutenance (1 min 30)** — `sara.bennani` → **Mes soutenances** : saisir le **PV et la note** de *Kenza*. Puis `nadia.alaoui` → **Soutenances** : valider le PV de *Mehdi* (15,5/20) ; montrer l'**export des notes** (CSV pour WebAurion).
6. **L'IA (45 s)** — `yasmine.benali` → la **bulle d'assistant** (en bas à droite) : l'ouvrir, poser une question (« Ma fiche a été refusée, que dois-je faire ? ») ; puis, dans **Mon stage → Modifier**, le bouton **« Faire relire mon sujet par l'assistant »**. Montrer la mention « Généré par une IA » et le fait que **l'IA propose, l'encadrant décide**. Sans clé ou sans Internet, un « mode démonstration » prend le relais (voir [[15-IA]]).
7. **Les coulisses (30 s)** — rappels et relances automatiques par e-mail (commande quotidienne `taches_quotidiennes`), l'**Administration** (en orange), l'import CSV depuis WebAurion et Moodle.
8. **Conclusion (30 s)** — 23 user stories couvertes, 296 tests automatiques, protection des données (loi 09-08). **Reste** : hébergement et serveur d'e-mails (avec le service informatique), charte graphique officielle.

## 3 bis. La clé de l'IA sur le PC de la démo
L'assistant marche **sans clé** (mode démonstration). Pour montrer la vraie IA : copier le fichier `cle_gemini.txt` (une ligne, la clé) dans le dossier `app/` du PC de démo, relancer, et **le supprimer après la présentation** (puis supprimer la clé dans Google AI Studio). Ce fichier n'est **jamais** dans l'archive ni sur GitHub. Il faut Internet pendant la démo pour la vraie IA. N'utiliser que des données fictives.

## 4. Si quelque chose ne marche pas
| Problème | Solution |
|---|---|
| « Python est introuvable » | Installer Python (voir §1), cocher « Add to PATH », relancer. |
| L'installation échoue (réseau, proxy de l'école) | Partager la connexion du téléphone et relancer. |
| « Port 8000 déjà utilisé » | Une ancienne fenêtre est encore ouverte : la fermer, relancer. |
| Page blanche ou ancien aspect | `Ctrl + F5` dans le navigateur. |
| Les données sont « abîmées » après des essais | Supprimer `demo.sqlite3`, relancer `LANCER_LA_DEMO.bat`. |
| Rien ne marche | Plan B : montrer la vidéo de la démo Copilot du dépôt d'Enzo et expliquer ce que la vraie version ajoute. |

## 5. Ce que fait le lancement (pour curieux)
`LANCER_LA_DEMO.bat` → crée l'environnement Python (`.venv`) → installe `requirements.txt` → `migrate` (crée la base) → `preparer_demo` (comptes et dossiers fictifs, avec les vraies fonctions de l'application) → ouvre le navigateur → `runserver`. Code : `app/comptes/management/commands/preparer_demo.py` (refuse de tourner en ligne : mot de passe connu de tous).
