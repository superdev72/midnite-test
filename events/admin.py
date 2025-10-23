from django.contrib import admin
from .models import User, Event


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model."""

    list_display = ["id", "name", "email", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "email"]
    ordering = ["name"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for Event model."""

    list_display = ["id", "user", "transaction_type", "amount", "timestamp", "created_at"]
    list_filter = ["transaction_type", "created_at", "user"]
    search_fields = ["user__name", "user__email"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at"]
