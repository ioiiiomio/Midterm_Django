from django.urls import path

from . import views


app_name = "library"

urlpatterns = [
    path("", views.resource_list, name="list"),
    path("upload/", views.resource_create, name="resource_create"),
    path("<int:pk>/", views.resource_detail, name="resource_detail"),
    path("<int:pk>/edit/", views.resource_update, name="resource_update"),
    path("<int:pk>/delete/", views.resource_delete, name="resource_delete"),
    path("<int:pk>/download/", views.resource_download, name="resource_download"),
]
