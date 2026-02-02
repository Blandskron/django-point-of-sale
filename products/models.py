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