from django.contrib.auth.forms import UserCreationForm
from django.forms import ChoiceField

from apps.users.models import User


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = (
    (User.Role.STUDENT, "student"),
    (User.Role.TUTOR, "tutor"),
    )

    role = ChoiceField(
        required=True,
        choices=ROLE_CHOICES,
    )

    def clean_email(self) -> str:
        return self.cleaned_data["email"].lower()

    class Meta:

        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "role",
        )
