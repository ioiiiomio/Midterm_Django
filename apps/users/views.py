from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from apps.users.forms import ProfileForm, RegisterForm
from apps.users.models import User

class RegisterView(CreateView):
    """Registration page. After sign up the user is logged in."""

    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form: RegisterForm) -> HttpResponse:
        """Save the new user and log them in."""
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    """Shows the logged in user's profile."""

    template_name = "users/profile.html"


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit the logged in user's profile."""

    form_class = ProfileForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset: QuerySet | None = None) -> User:
        """Always edit the current user, never someone else."""
        return self.request.user


def home(request: HttpRequest) -> HttpResponse:
    """Main page."""
    return render(request, "home.html")
