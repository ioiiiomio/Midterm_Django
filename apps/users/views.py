from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from apps.users.forms import RegisterForm


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


def home(request: HttpRequest) -> HttpResponse:
    """Main page."""
    return render(request, "home.html")
