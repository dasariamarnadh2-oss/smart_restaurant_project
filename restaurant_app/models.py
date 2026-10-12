from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=80, blank=True, help_text="Optional Bootstrap Icons class, e.g. bi bi-cup-hot")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    is_vegetarian = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)

    class Meta:
        ordering = ["category__name", "name"]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gt=0), name="menu_item_price_positive")
        ]

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "Received", "Received"
        PREPARING = "Preparing", "Preparing"
        READY = "Ready", "Ready"
        COMPLETED = "Completed", "Completed"

    customer_name = models.CharField(max_length=120)
    table_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RECEIVED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name="order_item_quantity_positive"),
            models.CheckConstraint(condition=models.Q(price__gt=0), name="order_item_price_positive"),
        ]

    @property
    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} × {self.menu_item.name}"
