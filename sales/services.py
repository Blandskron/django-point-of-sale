from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Sale, SaleItem

TAX_RATE = Decimal("0.19")

@transaction.atomic
def create_sale(user, cart):
    subtotal = Decimal("0.0")

    for item in cart:
        product = item["product"]
        qty = item["quantity"]

        if product.product_type == "STOCK":
            if product.stock < qty:
                raise ValidationError("Stock insuficiente")
            product.stock -= qty
            product.save()

        subtotal += product.price * qty

    tax = subtotal * TAX_RATE
    total = subtotal + tax

    sale = Sale.objects.create(
        user=user,
        subtotal=subtotal,
        tax=tax,
        total=total,
    )

    for item in cart:
        SaleItem.objects.create(
            sale=sale,
            product=item["product"],
            quantity=item["quantity"],
            unit_price=item["product"].price,
            total_price=item["product"].price * item["quantity"],
        )

    return sale