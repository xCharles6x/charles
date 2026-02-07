from django.contrib import admin
from .models import Profile, Product, Cart, Conversation, Message, Rating, ProductView


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'location', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'location']
    readonly_fields = ['created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'condition', 'seller', 'is_available', 'views_count', 'created_at']
    list_filter = ['category', 'condition', 'is_available', 'created_at']
    search_fields = ['name', 'description', 'seller__username']
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    list_editable = ['is_available']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'product', 'quantity', 'added_at']
    list_filter = ['added_at']
    search_fields = ['buyer__username', 'product__name']
    readonly_fields = ['added_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['product', 'buyer', 'seller', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['product__name', 'buyer__username', 'seller__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'conversation', 'timestamp', 'read']
    list_filter = ['read', 'timestamp']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['timestamp']
    list_editable = ['read']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['seller', 'buyer', 'product', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['seller__username', 'buyer__username', 'product__name', 'review']
    readonly_fields = ['created_at']


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['viewed_at']
