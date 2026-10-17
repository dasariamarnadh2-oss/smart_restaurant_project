from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from restaurant_app.models import MenuItem


class Command(BaseCommand):
    help = "Load the initial restaurant menu when the database has no menu items."

    @transaction.atomic
    def handle(self, *args, **options):
        if MenuItem.objects.exists():
            self.stdout.write("Menu items already exist; initial menu was not loaded.")
            return

        call_command("loaddata", "initial_menu", verbosity=0)
        count = MenuItem.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Loaded {count} initial menu items."))
