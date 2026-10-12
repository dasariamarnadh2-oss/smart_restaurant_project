# Generated initial migration for the restaurant app.
import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("icon", models.CharField(blank=True, help_text="Optional Bootstrap Icons class, e.g. bi bi-cup-hot", max_length=80)),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "categories"},
        ),
        migrations.CreateModel(
            name="MenuItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=9, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("is_vegetarian", models.BooleanField(default=True)),
                ("is_available", models.BooleanField(default=True)),
                ("image_url", models.URLField(blank=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="items", to="restaurant_app.category")),
            ],
            options={"ordering": ["category__name", "name"]},
        ),
        migrations.AddConstraint(
            model_name="menuitem",
            constraint=models.CheckConstraint(condition=models.Q(("price__gt", 0)), name="menu_item_price_positive"),
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer_name", models.CharField(max_length=120)),
                ("table_number", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("status", models.CharField(choices=[("Received", "Received"), ("Preparing", "Preparing"), ("Ready", "Ready"), ("Completed", "Completed")], default="Received", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("price", models.DecimalField(decimal_places=2, max_digits=9, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("menu_item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="restaurant_app.menuitem")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="restaurant_app.order")),
            ],
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(condition=models.Q(("quantity__gte", 1)), name="order_item_quantity_positive"),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(condition=models.Q(("price__gt", 0)), name="order_item_price_positive"),
        ),
    ]
