# 09 — Prochaines étapes (proposition)

Retour : [[Accueil]] · Décisions : [[08-Decisions-ouvertes]]

> Feuille de route **proposée par Claude**, à valider par Walid. Chaque étape suit la règle « plan court → OK de Walid → réalisation → test → journal » ([[10-Workflow-Claude-Code]]).

## Avant de coder
0. ✔ Organisation du dossier décidée : code dans `app/`, **travail en local pour l'instant** (2026-10-12). Conseillé : `git init` local pour pouvoir revenir en arrière, sans rien publier. Dépôt GitHub du groupe : plus tard (voir [[10-Workflow-Claude-Code]] et [[08-Decisions-ouvertes]] #17).
0bis. ✔ Processus réel clarifié (2026-10-12) : pas de Responsable, pas de validation à 3 niveaux, affectation de l'encadrant par le Service Stages (voir [[02-Processus-BPMN]]).
1. Trancher la **forme de l'application et la stack** (décisions #1 à #4). Claude peut préparer un comparatif court.
2. Parler à Wael et au groupe : matrice MoSCoW, stack, taille du groupe.
3. Ouvrir ce dossier dans Claude Code, vérifier qu'il lit bien `CLAUDE.md`, et lui demander un état des lieux en 10 lignes.

## Ordre de construction suggéré
Chaque lot donne un résultat que l'on peut montrer, comme dans la démo.
*Mode de travail depuis le 2026-10-14 : un plan par lot, le lot construit d'une traite, un bilan à la fin (voir `CLAUDE.md`).*
- ✅ **Lot 0 — Squelette** : projet, base de données, comptes de test, connexion, rôles, un écran par rôle (vide).
- ✅ **Lot 1 — Fiche de stage** : US-23 (affectation de l'encadrant), US-01 et US-02 (brouillon, soumission, validation pédagogique avec motif).
- ✅ **Lot 2 — Convention** : US-03, US-04 et US-05 (PDF à partir de la fiche, émission par le Career Center avec la signature du directeur des études, **signature papier puis dépôt du scan**, historique).
- ✅ **Lot 3 bis — Livrables et rappels** *(remplace l'ancien Lot 3 « dépôt et correction sur la plateforme » : les livrables sont rendus sur **Moodle**)* : suivi des livrables par le Career Center, rappels automatiques (commande quotidienne `envoyer_rappels`), calendrier réglable. Ancien libellé du Lot 3 : US-09 (rapport final PDF horodaté, bloqué après la date limite), puis US-17 à US-19 (livrables et correction par l'encadrant).
- ✅ **Lot 4 — Pilotage et échanges** : tableau de bord du Career Center (US-11), import des étudiants et encadrants depuis WebAurion (US-08), export des conventions signées au format WebAurion (US-07), import Moodle des livrables rendus, archive ZIP du dossier (partie archivage d'US-16). Reste d'US-16 (export des notes, PV) : Lot 6. Formats CSV en hypothèses : voir [[08-Decisions-ouvertes]] #27.
- ✅ **Lot 5 — Notifications** : relances automatiques (US-06) des valideurs et des étudiants, avec récapitulatif au Career Center ; réglages SMTP et commande `tester_email`. Les rappels de livrables (US-10) étaient déjà faits au Lot 3 bis. **Le code est prêt, l'envoi réel attend un serveur SMTP** ([[08-Decisions-ouvertes]] #31).
- ✅ **Lot 6 — Soutenances** : campagne et sondage de disponibilités du jury (US-12), planning proposé automatiquement puis validé (US-13), convocations et mises à jour par e-mail (US-14), PV et note en ligne validés par le Career Center (US-15), export des notes en CSV, PV dans l'archive du dossier (US-16). Voir [[08-Decisions-ouvertes]] #32 et #33.
- ✅ **Lot 7 — Mise en ligne (préparation)** *(ajouté le 2026-10-14 ; remplace l'ancien « signature en ligne », la signature étant sur papier)* : réglages de production (HTTPS, cookies, refus de démarrer sans vraie clé secrète), PostgreSQL par `DATABASE_URL`, WhiteNoise et gunicorn, commandes `sauvegarder` et `restaurer`, mot de passe oublié et changement, protection des données (page publique, droit d'accès, anonymisation). **Le code est prêt ; l'installation réelle dépend de l'école** : voir [[12-Mise-en-ligne]], [[11-Protection-des-donnees]] et [[08-Decisions-ouvertes]] #34, #35.
- ✅ **Lot 8 — Refonte de l'interface (fait le 2026-10-15, voir `journal/journal.md`)** *(ajouté le 2026-10-15 à la demande de Walid)* : l'interface actuelle est volontairement minimale (CSS dans `base.html`) et **n'est pas l'interface finale voulue**. Une fois toutes les fonctions en place (lots 0 à 6) : choisir le style avec Walid et le groupe (maquettes `docs/04`), refaire les gabarits et la mise en page, vérifier l'accessibilité et l'affichage sur mobile. Aucun changement de logique métier attendu.
- **Optionnel** : offres partenaires US-20 à US-22 (et candidature des étudiants si décidé).
Ce découpage est une proposition ; l'ordre peut changer selon les besoins du cours.

## Chantiers de documents
- Mettre à jour le rapport S2 (stack, tables) quand la stack sera fixée.
- Ajouter un script de données de démo avec un **stage terminé** et un **vrai PDF**, pour pouvoir montrer le dépôt de rapport.
- Garder le dépôt propre : `.gitignore` (pas de `.sqlite`, `.env`, `node_modules`, `uploads/`).

## Livrables déjà faits (rappel)
S1 rendu · S2 rendu · S3 : MVP démo poussé et vidéo sous-titrée prête ([[07-MVP-demo-Copilot]]). On ne connaît pas encore la suite du calendrier du cours.
