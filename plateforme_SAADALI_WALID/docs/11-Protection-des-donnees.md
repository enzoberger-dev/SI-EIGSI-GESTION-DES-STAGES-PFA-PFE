# 11 — Protection des données personnelles

Retour : [[Accueil]] · Mise en ligne : [[12-Mise-en-ligne]] · Décisions : [[08-Decisions-ouvertes]]

> **Cette note est technique, ce n'est pas un avis juridique.** Elle décrit ce que la plateforme fait des données et ce qui est prévu pour respecter la loi marocaine **09-08** (protection des personnes physiques à l'égard du traitement des données à caractère personnel, contrôlée par la **CNDP**). Les durées et la formulation de la page d'information sont des **hypothèses à faire valider par l'école** ([[08-Decisions-ouvertes]] #34). La déclaration ou l'autorisation auprès de la CNDP est une démarche **de l'école** (responsable du traitement).

## Ce que la plateforme conserve
| Donnée | Où | Pourquoi | Qui y accède | Durée prévue |
|---|---|---|---|---|
| Nom, prénom, e-mail, rôle, mot de passe (chiffré, jamais en clair) | compte | se connecter, envoyer les e-mails | la personne ; le Career Center | tant que le compte est actif ; anonymisé 10 ans après la dernière inscription |
| Promotion, inscription, encadrant affecté | inscriptions, affectations | savoir qui valide le stage | Career Center, encadrant, étudiant | 10 ans |
| Entreprise, sujet, dates, tuteur et représentant (nom, e-mail, téléphone) | fiche de stage | convention, suivi | étudiant, valideur, Career Center | 10 ans ; coordonnées du tuteur effacées à l'anonymisation |
| Convention (PDF) et scan signé | fichiers (`uploads/`) | preuve de la convention | étudiant concerné, Career Center | 10 ans (article 13 de la convention) ; effacés à l'anonymisation |
| Livrables (nom, date limite, rendu ou non), rappels et relances envoyés | suivi | rappels automatiques | Career Center, étudiant | 10 ans |
| Historique des actions (qui, quoi, quand, motifs de refus) | historique | traçabilité | Career Center, valideur, étudiant | 10 ans |
| Soutenance : créneau, salle, jury, PV, note | soutenances | organiser, noter, archiver | jury (sa soutenance), Career Center ; étudiant (date et jury) | note : 10 ans ; texte du PV effacé à l'anonymisation |
| Disponibilités des membres du jury | soutenances | planifier | Career Center | durée de la campagne (à purger : voir « Points ouverts ») |

## Droits des personnes : comment y répondre
Toute demande arrive à l'adresse de contact de l'école (« Paramètres de l'école »). **Vérifier l'identité** de la personne avant de répondre.
- **Accès** : `manage.py donnees_personnelles adresse@ecole.ma` affiche tout ce qui est détenu (JSON). À transmettre uniquement à la personne.
- **Rectification** : le Career Center corrige dans `/admin/` (compte, fiche de stage).
- **Suppression / opposition** : si la loi le permet, anonymiser le compte (`manage.py anonymiser_comptes`, qui traite les comptes de plus de 10 ans ; pour une demande avant l'échéance, utiliser `--annees` avec une valeur plus petite **après avoir vérifié la liste affichée**, ou demander une intervention technique).
- **Délai de réponse** : fixé par l'école (la loi demande une réponse dans un délai raisonnable).

## Protections techniques en place
- Mots de passe chiffrés (jamais lisibles), règles de qualité (longueur, mots courants), changement et « mot de passe oublié » par lien à usage unique valable 24 h.
- Accès limité par rôle sur **chaque** page ; téléchargement des fichiers contrôlé personne par personne ; les fichiers de `uploads/` ne sont jamais servis directement.
- En ligne : HTTPS obligatoire, cookies sécurisés, en-têtes de sécurité, session de 12 h au plus (voir [[12-Mise-en-ligne]]).
- Exports CSV protégés contre l'injection de formules Excel.
- Les archives de **sauvegarde ne sont pas chiffrées** : elles doivent être stockées dans un endroit à accès restreint.
- Page d'information publique : `/protection-des-donnees/`, liée en bas de chaque page.

## Ce que l'école doit faire (hors code)
1. Désigner le **responsable du traitement** et le contact pour les demandes.
2. Faire la **déclaration / demande d'autorisation à la CNDP** et conserver le récépissé.
3. Vérifier la **page d'information** (`/protection-des-donnees/`) et les **durées de conservation**.
4. Encadrer l'**hébergeur** et le **fournisseur d'e-mails** (sous-traitants) : contrat, lieu de stockage des données. Vérifier si les données doivent rester au Maroc.
5. Décider qui peut faire une demande d'accès et comment l'identité est vérifiée.

## Points ouverts
- **Durée de 10 ans** : tirée de la convention ; à confirmer pour les notes et les PV (peut-être plus longue pour les dossiers académiques).
- **Données des entreprises et des tuteurs** : ce sont aussi des données personnelles (nom, e-mail, téléphone). Elles sont effacées à l'anonymisation de l'étudiant, mais pas avant.
- **Disponibilités des jurys, rappels et relances envoyés** : pas encore purgés automatiquement.
- **Sauvegardes** : une personne anonymisée reste présente dans les anciennes sauvegardes jusqu'à leur rotation (14 jours par défaut).
- **Mots de passe provisoires** : voir [[12-Mise-en-ligne]], §7.
