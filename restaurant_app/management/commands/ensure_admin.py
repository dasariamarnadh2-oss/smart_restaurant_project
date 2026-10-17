import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Ensure the configured Django administrator account exists."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "").strip()
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")

        if not username:
            raise CommandError("DJANGO_ADMIN_USERNAME must be configured.")
        if not password:
            raise CommandError("DJANGO_ADMIN_PASSWORD must be configured.")

        user_model = get_user_model()
        try:
            user = user_model._default_manager.get(username=username)
        except user_model.DoesNotExist:
            user_model._default_manager.create_superuser(
                username=username,
                email="",
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}'."))
            return

        if not user.is_active or not user.is_staff or not user.is_superuser:
            raise CommandError(
                f"'{username}' already exists but is not an active superuser."
            )

        self.stdout.write(f"Admin user '{username}' already exists.")
