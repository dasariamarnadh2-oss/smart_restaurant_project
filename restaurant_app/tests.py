from django.core.management import call_command
from django.test import TestCase

from restaurant_app.models import Category, MenuItem


class SeedMenuCommandTests(TestCase):
    def test_loads_initial_menu_when_empty(self):
        call_command("seed_menu")

        self.assertEqual(Category.objects.count(), 5)
        self.assertEqual(MenuItem.objects.count(), 22)
        self.assertTrue(
            MenuItem.objects.filter(name="Butter Chicken", is_available=True).exists()
        )

    def test_does_not_overwrite_existing_menu(self):
        category = Category.objects.create(name="Custom", icon="bi bi-grid")
        MenuItem.objects.create(
            category=category,
            name="Custom dish",
            description="A restaurant-specific dish.",
            price="125.00",
        )

        call_command("seed_menu")

        self.assertEqual(MenuItem.objects.count(), 1)
        self.assertTrue(MenuItem.objects.filter(name="Custom dish").exists())
