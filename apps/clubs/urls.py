from django.urls import path

from . import views


app_name = "clubs"

urlpatterns = [
    path("", views.club_list, name="list"),
    path("create/", views.club_create, name="create"),
    path("<int:pk>/", views.club_detail, name="detail"),
    path("<int:pk>/edit/", views.club_edit, name="edit"),
    path("<int:pk>/delete/", views.club_delete, name="delete"),
    path("<int:pk>/join/", views.join_request, name="join"),
    path(
        "request/<int:membership_id>/<str:action>/",
        views.manage_request,
        name="manage_request",
    ),
]
