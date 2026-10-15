from typing import Any

from django import forms
from django.core.exceptions import ValidationError

from apps.tutoring.models import Review, TutoringSession, TutorProfile
from apps.users.models import User


class TutorProfileForm(forms.ModelForm):
    class Meta:
        model = TutorProfile
        fields = (
            "headline",
            "bio",
            "subjects",
            "hourly_rate",
            "years_experience",
            "is_available",
        )
        widgets = {"subjects": forms.CheckboxSelectMultiple}


class TutoringSessionForm(forms.ModelForm):
    def __init__(self, *args: Any, user: User, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        profile = user.tutor_profile
        if self.instance._state.adding:
            self.instance.tutor = profile
        self.fields["subject"].queryset = profile.subjects.all()
        for field_name in ("starts_at", "ends_at"):
            self.fields[field_name].widget = forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            )
            self.fields[field_name].input_formats = ("%Y-%m-%dT%H:%M",)

    class Meta:
        model = TutoringSession
        fields = (
            "subject",
            "title",
            "description",
            "starts_at",
            "ends_at",
            "location",
            "meeting_url",
            "capacity",
        )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")

    def clean_rating(self) -> int:
        rating = self.cleaned_data["rating"]
        if not 1 <= rating <= 5:
            raise ValidationError("Choose a rating from 1 to 5.")
        return rating
