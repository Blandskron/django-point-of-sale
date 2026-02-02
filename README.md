Perfecto. A continuación tienes **TODO el código base funcional** del POS en Django, **listo para copiar y pegar**, sin diseño, sin JS innecesario y **pensado para prueba técnica**.
Incluye **models, views, urls, admin y templates base** por aplicación.

> Stack asumido: **Django 5.x**, templates clásicos, auth estándar.

---

# 📁 apps/accounts

## `apps/accounts/urls.py`

```python
from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
```

---

# 📁 apps/products

## `apps/products/models.py`

```python
from django.db import models

class Product(models.Model):
    PRODUCT_TYPE_CHOICES = (
        ("STOCK", "Producto con stock"),
        ("MANUAL", "Preparación manual"),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", null=True, blank=True)

    product_type = models.CharField(
        max_length=10,
        choices=PRODUCT_TYPE_CHOICES
    )

    stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Solo para productos con stock"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

---

## `apps/products/admin.py`

```python
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_type", "price", "stock", "is_active")
    list_filter = ("product_type", "is_active")
    search_fields = ("name",)
```

---

## `apps/products/views.py`

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Product

@login_required
def product_list(request):
    products = Product.objects.filter(is_active=True)
    return render(request, "pos/product_list.html", {"products": products})
```

---

## `apps/products/urls.py`

```python
from django.urls import path
from .views import product_list

urlpatterns = [
    path("", product_list, name="product_list"),
]
```

---

# 📁 apps/sales

## `apps/sales/models.py`

```python
from django.db import models
from django.contrib.auth.models import User

class Sale(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale #{self.id}"
```

---

## `apps/sales/models.py` (continuación)

```python
from apps.products.models import Product

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
```

---

## `apps/sales/admin.py`

```python
from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total", "created_at")
    inlines = [SaleItemInline]
```

---

## `apps/sales/services.py`

```python
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
```

---

## `apps/sales/views.py`

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from apps.products.models import Product
from .services import create_sale
from .models import Sale

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
```

---

## `apps/sales/urls.py`

```python
from django.urls import path
from .views import add_to_cart, view_cart, confirm_sale, receipt

urlpatterns = [
    path("cart/", view_cart, name="cart"),
    path("add/<int:product_id>/", add_to_cart, name="add_to_cart"),
    path("confirm/", confirm_sale, name="confirm_sale"),
    path("receipt/<int:sale_id>/", receipt, name="receipt"),
]
```

---

# 🌐 URLs principales

## `config/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.products.urls")),
    path("sales/", include("apps.sales.urls")),
    path("accounts/", include("apps.accounts.urls")),
]
```

---

# 🖼️ Templates base (HTML)

## `templates/base.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>POS</title>
</head>
<body>
    {% if user.is_authenticated %}
        <p>Usuario: {{ user.username }} |
        <a href="{% url 'logout' %}">Salir</a></p>
    {% endif %}
    <hr>
    {% block content %}{% endblock %}
</body>
</html>
```

---

## `templates/auth/login.html`

```html
{% extends "base.html" %}
{% block content %}
<h2>Login</h2>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Ingresar</button>
</form>
{% endblock %}
```

---

## `templates/pos/product_list.html`

```html
{% extends "base.html" %}
{% block content %}
<h2>Productos</h2>
<ul>
{% for product in products %}
    <li>
        {{ product.name }} - ${{ product.price }}
        <a href="{% url 'add_to_cart' product.id %}">Agregar</a>
    </li>
{% endfor %}
</ul>
<a href="{% url 'cart' %}">Ver carrito</a>
{% endblock %}
```

---

## `templates/pos/cart.html`

```html
{% extends "base.html" %}
{% block content %}
<h2>Carrito</h2>
<ul>
{% for item in cart %}
    <li>{{ item.product.name }} x {{ item.quantity }} = ${{ item.total }}</li>
{% endfor %}
</ul>
<a href="{% url 'confirm_sale' %}">Confirmar venta</a>
{% endblock %}
```

---

## `templates/pos/receipt.html`

```html
{% extends "base.html" %}
{% block content %}
<h2>Boleta #{{ sale.id }}</h2>
<p>Fecha: {{ sale.created_at }}</p>
<ul>
{% for item in sale.items.all %}
    <li>{{ item.product.name }} x {{ item.quantity }} = ${{ item.total_price }}</li>
{% endfor %}
</ul>
<p>Subtotal: ${{ sale.subtotal }}</p>
<p>IVA: ${{ sale.tax }}</p>
<p><strong>Total: ${{ sale.total }}</strong></p>
{% endblock %}
```

---

# ✅ Resultado

Con esto tienes:

* Login obligatorio
* POS funcional
* Productos con y sin stock
* Venta con impuestos
* Boleta persistida
* Código limpio, evaluable y defendible

Si quieres, el **siguiente nivel** sería:

* Tests
* Fixtures
* README de entrevista
* Docker
* API REST opcional

Dime y lo subimos otro escalón 🚀
