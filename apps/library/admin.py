from django.contrib import admin

from .models import Resource, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin settings for subjects."""

    list_display = ("name", "created_at", "deleted_at")
    search_fields = ("name",)
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin settings for resources."""

    list_display = (
        "title",
        "subject",
        "resource_type",
        "uploader",
        "created_at",
        "deleted_at",
    )
    search_fields = ("title", "description", "uploader__email")
    list_filter = ("subject", "resource_type", "created_at")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("subject", "uploader")
    list_per_page = 50
