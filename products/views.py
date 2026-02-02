from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from products.models import Product

TAX_RATE = Decimal("0.19")

@login_required
def product_list(request):
    products = Product.objects.filter(is_active=True)

    cart = request.session.get("cart", {})  # { "1": 2, "5": 1 }

    # Traer productos del carrito en una sola query
    ids = [int(pid) for pid in cart.keys()] if cart else []
    cart_products = Product.objects.filter(id__in=ids) if ids else []

    product_map = {p.id: p for p in cart_products}

    cart_items = []
    subtotal = Decimal("0.0")

    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = product_map.get(pid)
        if not product:
            continue

        qty_int = int(qty)
        line_total = product.price * qty_int
        subtotal += line_total

        cart_items.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "qty": qty_int,
            "line_total": line_total,
            "product_type": product.product_type,
        })

    tax = (subtotal * TAX_RATE) if subtotal > 0 else Decimal("0.0")
    total = subtotal + tax

    return render(request, "pos/product_list.html", {
        "products": products,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "tax_rate_percent": int(TAX_RATE * 100),
    })
