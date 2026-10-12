from django.urls import path
from . import views

app_name = "restaurant_app"

urlpatterns = [
    path("", views.menu, name="menu"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:item_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:order_id>/", views.order_track, name="order_track"),
    path("track/", views.track_lookup, name="track_lookup"),
    path("kitchen/", views.kitchen_dashboard, name="kitchen_dashboard"),
    path("kitchen/order/<int:order_id>/status/", views.update_order_status, name="update_order_status"),
]
