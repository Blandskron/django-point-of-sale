from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from .services import create_sale
from .models import Sale
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def clear_cart(request):
    request.session["cart"] = {}
    return redirect("product_list")

@login_required
def remove_one_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    key = str(product_id)
    if key in cart:
        cart[key] -= 1
        if cart[key] <= 0:
            del cart[key]
    request.session["cart"] = cart
    return redirect("product_list")

@login_required
def add_to_cart(request, product_id):
    cart = request.session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session["cart"] = cart
    return redirect("product_list")

@login_required
def view_cart(request):
    cart_data = []
    cart = request.session.get("cart", {})

    for product_id, qty in cart.items():
        product = Product.objects.get(id=product_id)
        cart_data.append({
            "product": product,
            "quantity": qty,
            "total": product.price * qty,
        })

    return render(request, "pos/cart.html", {"cart": cart_data})

@login_required
def confirm_sale(request):
    cart = request.session.get("cart", {})
    items = []

    for product_id, qty in cart.items():
        product = Product.objects.get(id=product_id)
        items.append({"product": product, "quantity": qty})

    sale = create_sale(request.user, items)
    request.session["cart"] = {}
    return redirect("receipt", sale_id=sale.id)

@login_required
def receipt(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    return render(request, "pos/receipt.html", {"sale": sale})