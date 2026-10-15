from django.urls import path

from . import views


app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("create/", views.event_create, name="create"),
    path("<int:pk>/", views.event_detail, name="detail"),
    path("<int:pk>/edit/", views.event_update, name="update"),
    path("<int:pk>/delete/", views.event_delete, name="delete"),
    path("<int:pk>/register/", views.event_register, name="register"),
    path("<int:pk>/cancel/", views.event_cancel, name="cancel"),
]
