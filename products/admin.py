from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_type", "price", "stock", "is_active")
    list_filter = ("product_type", "is_active")
    search_fields = ("name",)