from django.contrib import admin

# Register your models here.
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@register(User)
class UserAdmin(BaseUserAdmin):
    """User model admin configuration class."""

    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_display_links = (
        "id",
        "email",
    )
    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
    )
    ordering = ("id",)
    readonly_fields = (
        "last_login",
        "created_at",
        "updated_at",
    )
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    fieldsets = (
        (
            "General information",
            {"fields": ("email", "password", ("first_name", "last_name"), "role")},
        ),
        (
            "Permissions",
            {"fields": (("is_staff", "is_active", "is_superuser"), "groups", "user_permissions")},
        ),
        (
            "Date and time information",
            {"fields": ("last_login", "created_at", "updated_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {"fields": ("email", ("first_name", "last_name"), "role", "password1", "password2")},
        ),
    )
    list_per_page = 50