from django import forms

from .models import Club, Membership


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["name", "description", "category", "logo"]
        help_texts = {
           "name": "Name of the Club",
            "description": "Description of the Club",
            "category": "Category of the Club",
        }


class MembershipRequestForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = []
