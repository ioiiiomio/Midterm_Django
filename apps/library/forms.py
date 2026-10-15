from typing import Any

from django.forms import ModelForm

from .models import Resource, Subject


class ResourceForm(ModelForm):
    """Upload / edit form. The uploader is set in the view, not here."""

    class Meta:
        model = Resource
        fields = ("title", "description", "file", "resource_type", "subject")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(deleted_at__isnull=True)
