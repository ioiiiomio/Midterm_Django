from datetime import datetime

from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    """Organizer is assigned by the server, never accepted from the browser."""

    # Declare the field so admin does not replace it with SplitDateTimeField
    # while retaining our single datetime-local widget.
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
        help_text="Enter local campus time (Asia/Almaty).",
    )

    def clean_date(self) -> datetime:
        date = self.cleaned_data["date"]
        previous = self.instance.date
        # The browser displays minutes. Preserve seconds for an unchanged date,
        # including historical events whose description/location needs correction.
        if self.instance.pk and previous and date == previous.replace(second=0, microsecond=0):
            return previous
        return date

    class Meta:
        model = Event
        fields = ("title", "description", "date", "location", "category", "capacity")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class EventFilterForm(forms.Form):
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    category = forms.ChoiceField(
        required=False,
        choices=[("", "All categories"), *Event.Category.choices],
    )
