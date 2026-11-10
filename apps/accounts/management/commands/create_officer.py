from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create a placement officer account."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--full-name", required=True)

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise CommandError("An account with that email already exists.")
        password = getpass("Password: ")
        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            raise CommandError("The passwords do not match.")
        try:
            validate_password(password)
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        User.objects.create_user(
            email=email,
            password=password,
            full_name=options["full_name"].strip(),
            role=User.Role.OFFICER,
            is_staff=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Created placement officer {email}."))
