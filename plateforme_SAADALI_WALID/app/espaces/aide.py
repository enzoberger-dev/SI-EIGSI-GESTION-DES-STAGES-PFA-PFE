"""
Textes de la page « Aide » (lot 8) : à quoi sert le site et comment l'utiliser, rôle par rôle.

Chaque personne ne voit que les sections de SES rôles (voir la vue `aide` dans views.py).
Les textes suivent le processus décidé (docs/02-Processus-BPMN.md) : ils sont à relire par le Career Center.
Un lien est un couple (texte du lien, nom de la page) ; le nom est transformé en adresse par la vue.
"""

from comptes import roles

INTRODUCTION = (
    "Cette plateforme suit les stages PFA et PFE de l'EIGSI Casablanca, de la déclaration du stage jusqu'à la "
    "soutenance. Elle remplace les e-mails, les saisies à la main et les relances : chacun voit où en est le "
    "dossier et ce qu'il doit faire. Ci-dessous, uniquement ce qui concerne votre rôle."
)

AIDE = {
    roles.ETUDIANT: {
        "resume": "Vous déclarez votre stage, puis vous suivez votre dossier jusqu'à la soutenance.",
        "etapes": [
            {"titre": "Déclarer votre stage",
             "texte": "Dans « Mon stage », renseignez l'entreprise, le sujet, les dates et votre tuteur. "
                      "Vous pouvez enregistrer un brouillon et y revenir plus tard.",
             "lien": ("Ouvrir Mon stage", "mon_stage")},
            {"titre": "Soumettre votre fiche",
             "texte": "Quand elle est complète, soumettez-la. Votre encadrant (ou le coordinateur de votre promotion) "
                      "l'examine et vous prévient par e-mail. Si elle est refusée, le motif apparaît dans l'historique : "
                      "corrigez puis soumettez de nouveau."},
            {"titre": "Signer la convention",
             "texte": "Une fois le stage validé, le Career Center prépare votre convention et la fait signer par le "
                      "directeur des études. Téléchargez-la dans « Mon stage », faites-la signer par l'entreprise et "
                      "signez-la, puis déposez le scan (PDF, JPG ou PNG, 10 Mo maximum)."},
            {"titre": "Rendre vos livrables",
             "texte": "Les livrables se rendent sur Moodle. La plateforme affiche les dates limites et vous envoie "
                      "des rappels par e-mail avant l'échéance, puis en cas de retard."},
            {"titre": "Passer votre soutenance",
             "texte": "Quand elle est planifiée, vous recevez une convocation. La date, la salle et le jury "
                      "apparaissent dans « Mon stage »."},
        ],
        "faq": [
            ("Ma fiche a été refusée, que faire ?",
             "Ouvrez « Mon stage » : le motif du refus est dans l'historique. Corrigez la fiche, puis soumettez-la à nouveau."),
            ("Je ne trouve pas ma convention.",
             "Elle apparaît dans « Mon stage » dès que le Career Center l'a générée. Elle ne se télécharge qu'après "
             "sa signature par le directeur des études. En cas de doute, contactez le Career Center."),
            ("Je n'ai pas d'encadrant.",
             "En 4e et 5e année, c'est le Career Center qui affecte un encadrant. Les autres années, le coordinateur "
             "de promotion valide votre fiche."),
            ("J'ai oublié mon mot de passe.",
             "Sur la page de connexion, « Mot de passe oublié ? » vous envoie un lien valable 24 heures."),
        ],
    },

    roles.ENCADRANT: {
        "resume": "Vous validez les fiches de stage de vos étudiants.",
        "etapes": [
            {"titre": "Examiner les fiches soumises",
             "texte": "Les fiches de vos étudiants apparaissent dans « Stages à valider ».",
             "lien": ("Ouvrir Stages à valider", "stages_a_valider")},
            {"titre": "Décider",
             "texte": "Validez la fiche, ou refusez-la en indiquant un motif (obligatoire) : l'étudiant le lit, corrige "
                      "et soumet de nouveau."},
            {"titre": "Ne pas laisser attendre",
             "texte": "Sans décision après quelques jours, la plateforme vous envoie une relance par e-mail avec un "
                      "lien direct vers la fiche."},
            {"titre": "Retrouver vos décisions",
             "texte": "Vos dernières décisions sont listées en bas de « Stages à valider »."},
        ],
        "faq": [
            ("Que mettre comme motif de refus ?",
             "Dites précisément ce qu'il faut corriger (sujet trop vague, dates incohérentes…) : l'étudiant le lira tel quel."),
            ("Je suis aussi membre du jury.",
             "Votre espace Jury apparaît dans le menu, avec ses propres explications dans cette page."),
        ],
    },

    roles.COORDINATEUR: {
        "resume": "Vous validez les fiches de stage des étudiants de votre promotion (1re à 3e année).",
        "etapes": [
            {"titre": "Examiner les fiches soumises",
             "texte": "Les fiches des étudiants de votre promotion apparaissent dans « Stages à valider ».",
             "lien": ("Ouvrir Stages à valider", "stages_a_valider")},
            {"titre": "Décider",
             "texte": "Validez la fiche, ou refusez-la en indiquant un motif (obligatoire) : l'étudiant le lit, corrige "
                      "et soumet de nouveau."},
            {"titre": "Ne pas laisser attendre",
             "texte": "Sans décision après quelques jours, la plateforme vous envoie une relance par e-mail."},
        ],
        "faq": [
            ("Que mettre comme motif de refus ?",
             "Dites précisément ce qu'il faut corriger : l'étudiant le lira tel quel."),
        ],
    },

    roles.SERVICE_STAGES: {
        "resume": "Vous pilotez l'ensemble : affectations, conventions, livrables, soutenances.",
        "etapes": [
            {"titre": "Suivre l'ensemble des dossiers",
             "texte": "Le tableau de bord montre ce qui est à traiter maintenant et où en sont les étudiants.",
             "lien": ("Ouvrir le tableau de bord", "tableau_de_bord")},
            {"titre": "Affecter les encadrants",
             "texte": "Les étudiants de 4e et 5e année ont besoin d'un encadrant : affectez-le ici.",
             "lien": ("Affecter les encadrants", "affectations")},
            {"titre": "Gérer les conventions",
             "texte": "Générez la convention d'un stage validé, faites-la signer par le directeur des études, cliquez sur "
                      "« Envoyer à l'étudiant », puis vérifiez le scan déposé : validez-le, ou refusez-le avec un motif.",
             "lien": ("Ouvrir Conventions", "conventions")},
            {"titre": "Suivre les livrables",
             "texte": "Marquez un livrable comme rendu après vérification sur Moodle, ou prolongez une date limite.",
             "lien": ("Ouvrir le suivi", "suivi")},
            {"titre": "Importer les données",
             "texte": "Importez la liste des étudiants (fichier CSV de WebAurion), puis l'état des rendus (CSV de Moodle). "
                      "Commencez par la simulation : elle n'enregistre rien et montre ce qui serait fait.",
             "lien": ("Importer depuis WebAurion", "import_webaurion")},
            {"titre": "Organiser les soutenances",
             "texte": "Créez une campagne, laissez les jurys indiquer leurs disponibilités, proposez le planning, "
                      "corrigez si besoin puis validez : les convocations partent. Validez ensuite les PV et les notes.",
             "lien": ("Ouvrir Soutenances", "soutenances")},
            {"titre": "Configurer la plateforme",
             "texte": "Comptes, promotions, entreprises, modèles de livrables et paramètres de l'école se gèrent dans "
                      "l'Administration (visible dans le menu si votre compte y a accès)."},
        ],
        "faq": [
            ("Un fichier CSV est refusé, pourquoi ?",
             "Le message d'erreur indique la ligne et la colonne en cause. Vérifiez les colonnes attendues puis "
             "relancez d'abord la simulation."),
            ("Comment envoyer les conventions signées à WebAurion ?",
             "Dans « Conventions », en bas de page : « Exporter les conventions signées (CSV pour WebAurion) »."),
            ("Un étudiant n'a plus accès à son compte.",
             "Il peut utiliser « Mot de passe oublié ? ». Sinon, créez ou réinitialisez son compte dans l'Administration."),
        ],
    },

    roles.JURY: {
        "resume": "Vous indiquez vos disponibilités, puis vous saisissez le PV et la note de chaque soutenance.",
        "etapes": [
            {"titre": "Indiquer vos disponibilités",
             "texte": "Quand une campagne de soutenances s'ouvre, vous recevez un e-mail avec un lien : cochez les "
                      "créneaux où vous êtes disponible.",
             "lien": ("Ouvrir Mes soutenances", "jury_accueil")},
            {"titre": "Consulter vos soutenances",
             "texte": "Une fois le planning validé, vous recevez une convocation. Vos soutenances sont listées avec la "
                      "date, la salle et l'étudiant."},
            {"titre": "Saisir le PV et la note",
             "texte": "Après la soutenance, saisissez le PV et la note sur 20. Vous pouvez les corriger tant que le "
                      "Career Center ne les a pas validés."},
        ],
        "faq": [
            ("Je dois modifier mes disponibilités.",
             "Tant que la campagne est ouverte, changez vos cases. Après, contactez le Career Center."),
            ("Le Career Center a renvoyé mon PV.",
             "Le motif est indiqué : corrigez le PV puis enregistrez-le de nouveau."),
        ],
    },
}
