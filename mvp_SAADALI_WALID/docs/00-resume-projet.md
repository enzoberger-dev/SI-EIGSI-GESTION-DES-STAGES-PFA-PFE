# Résumé du projet

## 1. Résumé de l’application

1. L’application doit centraliser la gestion des stages PFA et PFE de l’EIGSI Casablanca.
2. L’étudiant déclare un stage trouvé, puis son encadrant vérifie sa conformité.
3. Une convention est générée, contrôlée par trois niveaux, puis signée par les parties.
4. La plateforme suit les livrables et le rapport, et permet les retours de l’encadrant.
5. Elle aide à organiser les soutenances, enregistrer leurs résultats et archiver les dossiers.
6. Elle prévoit des rappels par e-mail, un tableau de bord et des échanges CSV avec WebAurion.
7. Un module facultatif permet aux entreprises de proposer des offres, ensuite modérées par l’école.
8. La solution technique proposée est une application web React, Node.js et PostgreSQL.

## 2. Fichiers trouvés et éléments manquants

| Fichier trouvé | Contenu |
| --- | --- |
| `README.md` | Très courte présentation du projet. |
| `S1_Rapport_Gestion_des_stages_PFE_PFA.pdf` | Premier rapport : contexte, SWOT, processus existant, priorités MoSCoW et indicateurs. |
| `S2_Rapport_Gestion_des_stages_PFE_PFA.pdf` | Rapport de conception : 22 besoins sous forme de récits utilisateurs, six maquettes, proposition technique, modèle de données et dictionnaire de données. |
| `BPMN_TO-BE.pdf` | Huit pages de schémas des processus cibles : déclaration, convention, suivi, soutenance et offres partenaires. |

Les maquettes, le backlog et le schéma de données sont intégrés au rapport S2 : il n’y a pas de fichiers séparés et modifiables pour ces éléments, ni de script SQL. Le dossier ne contient pas de code de l’application, de tests ou de fichiers de configuration permettant de la lancer. Le choix de la technologie est présenté comme une proposition à confirmer. Les maquettes indiquent que l’espace Jury et le module d’offres ne sont pas encore dessinés.

## 3. Écarts et points à clarifier

- **Offres et candidatures : priorité et périmètre différents.** Le rapport S1 classe les offres d’entreprises et la candidature des étudiants parmi les fonctions indispensables. Dans le rapport S2, les offres deviennent facultatives (« Could ») et les étudiants sont censés trouver leur stage par leurs propres moyens. Le parcours de candidature n’apparaît plus dans les récits utilisateurs.
- **Évaluation par l’entreprise absente du backlog et des données.** Le BPMN prévoit une fiche d’évaluation remplie par l’entreprise à la fin du stage, et le rapport S1 parle aussi d’évaluations des tuteurs. Le backlog S2 ne décrit pas clairement cette fonction et le modèle de données ne montre pas de table ou de champs dédiés à cette évaluation.
- **Procès-verbal de soutenance à représenter dans les données.** Le récit utilisateur US-15 et le BPMN prévoient la saisie du PV, sa validation, son rattachement au dossier et son archivage. Dans le dictionnaire S2, la table `SOUTENANCE` décrit la date, la salle et la note, mais pas le fichier ou le contenu du PV.
- **Lien entre le modèle et son dictionnaire incomplet.** Le schéma annonce 12 tables et montre une table d’association entre jury et soutenance (`jury_soutenance`), mais cette table n’a pas d’entrée dédiée dans le dictionnaire de données. Son rôle et les liens entre jury, étudiant et soutenance restent donc à préciser.
- **Fonctions prévues mais sans maquette.** Le rapport S2 signale que l’espace Jury (disponibilités, PV) et les écrans du module d’offres ne sont pas maquettés, alors que ces fonctions figurent dans le backlog.
- **Signature à faire valider.** Le rapport S1 demande une signature électronique tripartite ; le rapport S2 propose une preuve par horodatage et empreinte SHA-256, en précisant que son acceptation par l’école reste à confirmer.

## 4. Questions pour avancer

1. Les étudiants doivent-ils pouvoir candidater aux offres dans la plateforme, et les offres sont-elles indispensables ou facultatives pour la première version ?
2. L’évaluation du stage par le tuteur de l’entreprise doit-elle être incluse ? Si oui, qui la saisit et comment l’entreprise accède-t-elle au formulaire ?
3. Le PV de soutenance doit-il être stocké comme fichier, saisi comme formulaire, ou les deux ?
4. L’école accepte-t-elle la signature proposée par horodatage et empreinte SHA-256, ou faut-il une autre forme de signature ?
5. La technologie proposée (React, Node.js, PostgreSQL) est-elle confirmée pour la réalisation ?
