from django.urls import path
from .views import add_to_cart, confirm_sale, receipt, clear_cart, remove_one_from_cart

urlpatterns = [
    path("add/<int:product_id>/", add_to_cart, name="add_to_cart"),
    path("remove-one/<int:product_id>/", remove_one_from_cart, name="remove_one_from_cart"),
    path("clear/", clear_cart, name="clear_cart"),
    path("confirm/", confirm_sale, name="confirm_sale"),
    path("receipt/<int:sale_id>/", receipt, name="receipt"),
]
