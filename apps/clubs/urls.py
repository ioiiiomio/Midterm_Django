from django.urls import path

from . import views


urlpatterns = [
    path("", views.club_list, name="club_list"),
    path("create/", views.club_create, name="club_create"),
    path("<int:pk>/", views.club_detail, name="club_detail"),
    path("<int:pk>/edit/", views.club_edit, name="club_edit"),
    path("<int:pk>/delete/", views.club_delete, name="club_delete"),
    path("<int:pk>/join/", views.join_request, name="join_request"),
    path(
        "request/<int:membership_id>/<str:action>/",
        views.manage_request,
        name="manage_request",
    ),
]
