# 14 — GitHub pour débutant, et où déposer la plateforme

> Mémo écrit pour Walid (2026-10-15). Lié à : [[10-Workflow-Claude-Code]], [[13-Demo-presentation]], [[08-Decisions-ouvertes]] #17.

## 1. Le vocabulaire en 10 lignes
| Mot | Ce que c'est |
|---|---|
| **Git** | L'outil installé sur ton PC qui garde l'historique de tes fichiers (chaque « commit » est une photo datée). Il marche sans Internet. |
| **GitHub** | Un site qui héberge des dépôts Git pour les partager. Git et GitHub sont deux choses différentes. |
| **Dépôt (repository)** | Un dossier de projet suivi par Git, avec tout son historique. |
| **Clone** | Copier un dépôt GitHub sur ton PC. |
| **Commit** | Une sauvegarde nommée (« feat: page d'aide »). Reste locale tant qu'on ne pousse pas. |
| **Push / Pull** | Envoyer tes commits vers GitHub / récupérer ceux des autres. |
| **Branche (branch)** | Une ligne de travail parallèle. `main` est la version « officielle » ; on travaille sur une autre branche pour ne rien casser. |
| **Pull request (PR)** | Une demande : « voici ma branche, voulez-vous la fusionner dans `main` ? » On y voit les changements, on peut commenter, puis **fusionner (merge)**. |
| **Collaborateur** | Quelqu'un à qui le propriétaire a donné le droit d'écrire dans son dépôt (ton cas dans le dépôt d'Enzo). |
| **Fork** | Une copie du dépôt dans *ton* compte, pour proposer des changements à un dépôt où tu n'as pas le droit d'écrire. Inutile pour toi : tu es collaborateur. |

## 2. Les autres fonctions utiles de GitHub
- **README.md** : la page d'accueil du dépôt (ce que le prof voit en premier). À soigner.
- **.gitignore** : la liste de ce qu'on ne met *jamais* dans le dépôt (bases de données, mots de passe, `.venv`). Déjà en place chez toi.
- **Issues** : une liste de tâches ou de bugs (« à faire : relire les textes d'aide »). Pratique en groupe.
- **Releases** : une version figée téléchargeable (par exemple « v1.0 démo du 16/10 » avec le ZIP).
- **Actions** : des vérifications automatiques à chaque envoi (par exemple lancer les 275 tests). Gratuit pour un dépôt public.
- **Pages** : un petit site web gratuit à partir du dépôt (pour une vitrine ; pas pour l'application, qui a besoin d'un serveur).
- **Historique et blame** : voir qui a changé quelle ligne, quand. Les commits montrent le travail de chacun.

## 3. Où déposer la plateforme : le dépôt d'Enzo
Ce que montrent tes notes : dépôt public `enzoberger-dev/SI-EIGSI-GESTION-DES-STAGES-PFA-PFE`, branches `main` et `wajih-démo`, avec déjà ton dossier `mvp_SAADALI_WALID/` et les rapports.

**Recommandation : un dossier à ton nom, envoyé sur une branche, puis une pull request.**
1. Créer la branche `walid-plateforme` dans ce dépôt.
2. Y ajouter un dossier **`plateforme_SAADALI_WALID/`** (même habitude que `mvp_SAADALI_WALID/`) contenant le code (`app/`), éventuellement les notes de conception (`docs/`) et le journal.
3. Ouvrir une **pull request** vers `main` : Enzo (administrateur du dépôt) voit exactement ce qui arrive, peut commenter, puis on **fusionne** avant la présentation pour que le prof le voie dans `main`.

Pourquoi pas directement dans `main` ? Techniquement, tu pourrais (tu as le droit d'écrire, et un dossier à part ne peut pas entrer en conflit avec les autres). Mais `main` est ce que le prof lit et ce que les autres modifient : passer par une branche te donne un aperçu avant publication, un retour en arrière facile, et c'est la méthode du travail en équipe (voir [[10-Workflow-Claude-Code]]).

Pourquoi un dossier et pas la racine ? Le dépôt contient déjà les rapports, la démo, le MVP et le travail de Wajih : un dossier par personne évite de tout mélanger.

**Pourquoi pas pousser l'historique de mon dépôt local tel quel ?** Les deux dépôts ont des histoires séparées (ils ne se sont jamais connus) : les fusionner serait pénible. On copie simplement les fichiers dans le dossier, avec un commit clair ; l'historique détaillé reste dans ton dépôt local.

## 4. Attention : le dépôt est PUBLIC
Tout ce qui est poussé est visible par tout le monde, et reste dans l'historique même si on le supprime ensuite.
- ✅ Vérifié : aucune base de données, aucun mot de passe réel, aucun fichier déposé, aucun `.env` dans ce qu'on envoie. Les comptes et entreprises de démonstration sont **fictifs** (`@example.test`).
- ⚠️ À décider par toi : `CLAUDE.md` (décrit l'équipe et ta façon de travailler) et `journal/` : utiles pour montrer la démarche, mais personnels. Ma proposition : envoyer `app/` et `docs/`, garder `CLAUDE.md` pour toi.
- ⚠️ Le mot de passe `Demo-EIGSI-2026` apparaîtra dans le dépôt public : sans danger (comptes fictifs qui n'existent que dans la base de démo, et la commande refuse de tourner en ligne).
- ⚠️ Les PDF du prof (`Prompts_prof_S3…pdf`) ne sont pas à republier.

## 5. Les commandes, pour comprendre (je peux les lancer à ta place)
```
git clone https://github.com/enzoberger-dev/SI-EIGSI-GESTION-DES-STAGES-PFA-PFE.git   # copie le dépôt sur le PC
git switch -c walid-plateforme                    # crée et ouvre ta branche
# (copier le dossier plateforme_SAADALI_WALID/ dedans)
git add plateforme_SAADALI_WALID                  # prépare les fichiers
git commit -m "feat: plateforme de gestion des stages (lots 0 à 8)"
git push -u origin walid-plateforme               # envoie la branche sur GitHub
# puis, sur github.com : bouton « Compare & pull request » → « Merge pull request »
```
**La première fois**, `git push` ouvre une fenêtre de connexion GitHub (navigateur) : c'est normal.

## 6. Et pour la démonstration ?
Le ZIP de la démo (voir [[13-Demo-presentation]]) est fait pour ne **pas** dépendre de GitHub : pas besoin de te connecter à ton compte sur le PC de Wael. Pour une démo à partir de GitHub, il suffirait de **télécharger le ZIP** du dépôt (bouton vert « Code » → « Download ZIP ») : sans compte, puisqu'il est public.
