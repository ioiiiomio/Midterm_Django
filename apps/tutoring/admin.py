from django.contrib import admin

from apps.tutoring.models import Booking, Review, Subject, TutoringSession, TutorProfile


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name", "description")


@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "hourly_rate", "is_available", "years_experience")
    list_filter = ("is_available", "subjects")
    search_fields = ("user__email", "user__first_name", "user__last_name", "headline")
    filter_horizontal = ("subjects",)
    autocomplete_fields = ("user",)


@admin.register(TutoringSession)
class TutoringSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "tutor", "subject", "starts_at", "ends_at", "capacity", "is_cancelled")
    list_filter = ("subject", "is_cancelled", "starts_at")
    search_fields = ("title", "tutor__user__email", "tutor__user__first_name", "subject__name")
    autocomplete_fields = ("tutor", "subject")
    date_hierarchy = "starts_at"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "created_at")
    list_filter = ("status", "session__subject", "session__starts_at")
    search_fields = ("student__email", "student__first_name", "session__title")
    autocomplete_fields = ("student", "session")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("booking", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("booking__student__email", "booking__session__tutor__user__email", "comment")
    autocomplete_fields = ("booking",)
