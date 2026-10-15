from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from apps.users.views import RegisterView


app_name = "users"

urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),
    path (
        "login/",
        LoginView.as_view(),
        name="login",
    ),
    path (
        "logout/",
        LogoutView.as_view(),
        name="logout",
    )
]
