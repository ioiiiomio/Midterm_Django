from django.contrib.auth.forms import UserCreationForm
from django.forms import ChoiceField, ModelForm

from apps.users.models import User


class RegisterForm(UserCreationForm):
    """Sign up form. Admin role can't be chosen here."""

    ROLE_CHOICES = (
        (User.Role.STUDENT, "Student"),
        (User.Role.TUTOR, "Tutor"),
    )

    role = ChoiceField(
        choices=ROLE_CHOICES,
    )

    class Meta:
        """Form settings."""

        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "role",
        )

    def clean_email(self) -> str:
        """Store emails in lowercase."""
        return self.cleaned_data["email"].lower()


class ProfileForm(ModelForm):
    """Edit own name. Email and role can't be changed here."""

    class Meta:
        """Form settings."""

        model = User
        fields = (
            "first_name",
            "last_name",
        )
