from django.contrib import admin
from django.db import transaction
from django.http import HttpRequest, HttpResponse

from .forms import EventForm
from .models import Event, EventRegistration
from .services import lock_event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventForm
    list_display = ("title", "date", "category", "organizer", "capacity", "deleted_at")
    search_fields = ("title", "description", "location", "organizer__email")
    list_filter = ("category", "date", "deleted_at")
    list_select_related = ("organizer",)
    readonly_fields = ("organizer", "created_at", "updated_at", "deleted_at")
    fields = (*EventForm.Meta.fields, *readonly_fields)
    date_hierarchy = "date"

    def save_model(self, request: HttpRequest, obj: Event, form: EventForm, change: bool) -> None:
        if not change:
            obj.organizer = request.user
        super().save_model(request, obj, form, change)

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict | None = None,
    ) -> HttpResponse:
        # Hold the same parent lock through validation and saving in admin too.
        with transaction.atomic():
            if request.method == "POST" and object_id and object_id.isdecimal():
                lock_event(int(object_id))
            return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ("event", "student", "registered_at", "deleted_at")
    search_fields = ("event__title", "student__email", "student__first_name", "student__last_name")
    list_filter = ("event__category", "registered_at", "deleted_at")
    list_select_related = ("event", "student")
    readonly_fields = (
        "event",
        "student",
        "registered_at",
        "created_at",
        "updated_at",
        "deleted_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Add through the event page so the capacity service cannot be bypassed.
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: EventRegistration | None = None
    ) -> bool:
        return False
