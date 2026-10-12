from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import CheckoutForm, OrderStatusForm
from .models import Category, MenuItem, Order, OrderItem

TAX_RATE = Decimal("0.05")


def _cart(session):
    raw = session.get("cart", {})
    # Ignore malformed session data rather than trusting it.
    cleaned = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            try:
                item_id, quantity = int(key), int(value)
                if item_id > 0 and 1 <= quantity <= 50:
                    cleaned[str(item_id)] = quantity
            except (TypeError, ValueError):
                continue
    session["cart"] = cleaned
    return cleaned


def _cart_details(session):
    cart_data = _cart(session)
    items = []
    subtotal = Decimal("0.00")
    stale_ids = []
    for item_id, quantity in cart_data.items():
        try:
            item = MenuItem.objects.get(pk=int(item_id), is_available=True)
        except MenuItem.DoesNotExist:
            stale_ids.append(item_id)
            continue
        line_total = (item.price * quantity).quantize(Decimal("0.01"))
        items.append({"item": item, "quantity": quantity, "line_total": line_total})
        subtotal += line_total
    for item_id in stale_ids:
        cart_data.pop(item_id, None)
    session["cart"] = cart_data
    tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return items, subtotal, tax, subtotal + tax


def menu(request):
    categories = Category.objects.prefetch_related("items")
    selected_category = request.GET.get("category", "").strip()
    vegetarian_only = request.GET.get("vegetarian") == "1"
    items = MenuItem.objects.filter(is_available=True).select_related("category")
    if selected_category:
        items = items.filter(category__name__iexact=selected_category)
    if vegetarian_only:
        items = items.filter(is_vegetarian=True)
    grouped = []
    for category in categories:
        category_items = [item for item in items if item.category_id == category.id]
        if category_items:
            grouped.append((category, category_items))
    cart_count = sum(_cart(request.session).values())
    return render(request, "restaurant_app/menu.html", {
        "grouped_items": grouped,
        "categories": categories,
        "selected_category": selected_category,
        "vegetarian_only": vegetarian_only,
        "cart_count": cart_count,
    })


def cart(request):
    items, subtotal, tax, grand_total = _cart_details(request.session)
    form = CheckoutForm()
    return render(request, "restaurant_app/cart.html", {
        "items": items, "subtotal": subtotal, "tax": tax,
        "grand_total": grand_total, "checkout_form": form,
    })


@require_POST
def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id, is_available=True)
    cart_data = _cart(request.session)
    key = str(item.pk)
    quantity = cart_data.get(key, 0)
    if quantity >= 50:
        messages.warning(request, "You can order up to 50 of each item.")
    else:
        cart_data[key] = quantity + 1
        request.session["cart"] = cart_data
        request.session.modified = True
        messages.success(request, f"{item.name} added to your cart.")
    return redirect(request.POST.get("next") or "restaurant_app:menu")


@require_POST
def update_cart(request, item_id):
    cart_data = _cart(request.session)
    key = str(item_id)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        quantity = 0
    item_exists = MenuItem.objects.filter(pk=item_id, is_available=True).exists()
    if not item_exists:
        cart_data.pop(key, None)
        messages.warning(request, "That menu item is no longer available.")
    elif quantity < 1 or quantity > 50:
        messages.error(request, "Quantity must be between 1 and 50.")
    else:
        cart_data[key] = quantity
        messages.success(request, "Cart updated.")
    request.session["cart"] = cart_data
    request.session.modified = True
    return redirect("restaurant_app:cart")


@require_POST
def remove_from_cart(request, item_id):
    cart_data = _cart(request.session)
    cart_data.pop(str(item_id), None)
    request.session["cart"] = cart_data
    request.session.modified = True
    messages.info(request, "Item removed from your cart.")
    return redirect("restaurant_app:cart")


@require_POST
def checkout(request):
    form = CheckoutForm(request.POST)
    items, subtotal, tax, grand_total = _cart_details(request.session)
    if not items:
        messages.error(request, "Your cart is empty or contains unavailable items.")
        return redirect("restaurant_app:cart")
    if not form.is_valid():
        return render(request, "restaurant_app/cart.html", {
            "items": items, "subtotal": subtotal, "tax": tax,
            "grand_total": grand_total, "checkout_form": form,
        }, status=400)

    with transaction.atomic():
        # Re-fetch and validate all menu items immediately before creating the order.
        cart_data = _cart(request.session)
        order_lines = []
        current_subtotal = Decimal("0.00")
        for item_id, quantity in cart_data.items():
            if quantity < 1 or quantity > 50:
                messages.error(request, "Invalid quantity in cart.")
                return redirect("restaurant_app:cart")
            item = MenuItem.objects.select_for_update().filter(pk=int(item_id), is_available=True).first()
            if item is None:
                messages.error(request, "A menu item became unavailable. Please review your cart.")
                return redirect("restaurant_app:cart")
            order_lines.append((item, quantity))
            current_subtotal += item.price * quantity

        current_subtotal = current_subtotal.quantize(Decimal("0.01"))
        current_tax = (current_subtotal * TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = current_subtotal + current_tax
        order = Order.objects.create(
            customer_name=form.cleaned_data["customer_name"],
            table_number=form.cleaned_data["table_number"],
            total_amount=total,
        )
        for item, quantity in order_lines:
            OrderItem.objects.create(order=order, menu_item=item, quantity=quantity, price=item.price)

    request.session["cart"] = {}
    request.session.modified = True
    messages.success(request, f"Order #{order.pk} placed successfully.")
    return redirect("restaurant_app:order_track", order_id=order.pk)


def order_track(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items__menu_item"), pk=order_id)
    steps = [Order.Status.RECEIVED, Order.Status.PREPARING, Order.Status.READY, Order.Status.COMPLETED]
    return render(request, "restaurant_app/order_track.html", {
        "order": order, "steps": steps, "current_step": steps.index(order.status),
    })


def track_lookup(request):
    if request.method == "POST":
        raw_id = request.POST.get("order_id", "").strip()
        if raw_id.isdigit() and int(raw_id) > 0:
            return redirect("restaurant_app:order_track", order_id=int(raw_id))
        messages.error(request, "Enter a valid order ID.")
    return render(request, "restaurant_app/order_track.html", {"lookup_only": True})


def staff_check(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(staff_check)
def kitchen_dashboard(request):
    orders = Order.objects.prefetch_related("items__menu_item").order_by("created_at")
    return render(request, "restaurant_app/kitchen_dashboard.html", {
        "orders": orders, "status_form": OrderStatusForm(),
    })


@login_required
@user_passes_test(staff_check)
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    form = OrderStatusForm(request.POST, instance=order)
    if form.is_valid():
        new_status = form.cleaned_data["status"]
        valid_next = {
            Order.Status.RECEIVED: {Order.Status.RECEIVED, Order.Status.PREPARING},
            Order.Status.PREPARING: {Order.Status.PREPARING, Order.Status.READY},
            Order.Status.READY: {Order.Status.READY, Order.Status.COMPLETED},
            Order.Status.COMPLETED: {Order.Status.COMPLETED},
        }
        if new_status in valid_next[order.status]:
            form.save()
            messages.success(request, f"Order #{order.pk} status updated.")
        else:
            messages.error(request, "Orders can only move forward through the kitchen workflow.")
    else:
        messages.error(request, "Choose a valid order status.")
    return redirect("restaurant_app:kitchen_dashboard")
