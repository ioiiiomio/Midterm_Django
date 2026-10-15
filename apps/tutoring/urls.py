from django.urls import path

from apps.tutoring.views import (
    BookingCancelView,
    BookingCreateView,
    MyBookingsView,
    MyScheduleView,
    ReviewCreateView,
    TutorDetailView,
    TutoringSessionCancelView,
    TutoringSessionCreateView,
    TutoringSessionUpdateView,
    TutorListView,
    TutorProfileEditView,
)


app_name = "tutoring"

urlpatterns = [
    path("", TutorListView.as_view(), name="tutor_list"),
    path("tutors/<int:pk>/", TutorDetailView.as_view(), name="tutor_detail"),
    path("profile/edit/", TutorProfileEditView.as_view(), name="profile_edit"),
    path("schedule/", MyScheduleView.as_view(), name="my_schedule"),
    path("schedule/add/", TutoringSessionCreateView.as_view(), name="session_add"),
    path("schedule/<int:pk>/edit/", TutoringSessionUpdateView.as_view(), name="session_edit"),
    path("schedule/<int:pk>/cancel/", TutoringSessionCancelView.as_view(), name="session_cancel"),
    path("bookings/", MyBookingsView.as_view(), name="my_bookings"),
    path("sessions/<int:session_id>/book/", BookingCreateView.as_view(), name="booking_create"),
    path("bookings/<int:pk>/cancel/", BookingCancelView.as_view(), name="booking_cancel"),
    path("bookings/<int:booking_id>/review/", ReviewCreateView.as_view(), name="review_create"),
]
