"""
Commande : python manage.py tester_email adresse@exemple.test

Envoie un message d'essai pour vérifier la configuration des e-mails. Affiche le mode utilisé :
- « console » (par défaut sur le PC) : le message s'affiche dans le terminal, rien ne part ;
- « SMTP » : le message part vraiment (réglages DJANGO_EMAIL_HOST, _PORT, _HOST_USER, _HOST_PASSWORD…,
  voir app/README.md). Le mot de passe n'est jamais affiché.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Envoie un e-mail d'essai pour vérifier la configuration."

    def add_arguments(self, parser):
        parser.add_argument("destinataire", help="Adresse qui recevra le message d'essai.")

    def handle(self, *args, **options):
        if settings.EMAIL_BACKEND.endswith("smtp.EmailBackend"):
            mode = f"SMTP ({settings.EMAIL_HOST}:{settings.EMAIL_PORT}, expéditeur {settings.DEFAULT_FROM_EMAIL})"
        elif settings.EMAIL_BACKEND.endswith("console.EmailBackend"):
            mode = "console (rien ne part : le message s'affiche ci-dessous)"
        else:
            mode = settings.EMAIL_BACKEND
        self.stdout.write(f"Mode d'envoi : {mode}")
        try:
            send_mail(
                "Essai : plateforme de gestion des stages",
                "Bonjour,\n\nSi vous lisez ce message, l'envoi d'e-mails de la plateforme fonctionne.\n",
                None, [options["destinataire"]],
            )
        except Exception as erreur:
            raise CommandError(f"Échec de l'envoi : {erreur}")
        self.stdout.write(self.style.SUCCESS("Message envoyé."))
