from django.contrib import admin
from .models import Category, Item, BorrowRequest

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'campus', 'status', 'is_available', 'created_at')
    list_filter = ('status', 'is_available', 'campus', 'category')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('item_id', 'created_at', 'updated_at')

@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ('item', 'borrower', 'lender', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('item__title', 'borrower__username', 'lender__username')
