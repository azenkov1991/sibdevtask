from django.contrib import admin
from .models import *

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', )


class ItemPriceInline(admin.TabularInline):
    model = ItemPrice


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', )
    inlines = [ItemPriceInline, ]


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['customer', 'item_price', 'quantity',]





