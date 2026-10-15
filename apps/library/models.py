from django.conf import settings
from django.db.models import (
    CASCADE,
    CharField,
    FileField,
    ForeignKey,
    TextChoices,
    TextField,
)

from apps.abstracts.models import AbstractBaseModel

from .validators import validate_file_extension, validate_file_size


class Subject(AbstractBaseModel):
    """Study subject, for example Linear Algebra."""

    name = CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Resource(AbstractBaseModel):
    """One uploaded study material."""

    class ResourceType(TextChoices):
        TEXTBOOK = "textbook", "Textbook"
        LECTURE_NOTES = "lecture_notes", "Lecture notes"
        PRESENTATION = "presentation", "Presentation"
        STUDY_GUIDE = "study_guide", "Study guide"

    title = CharField(max_length=200)
    description = TextField(blank=True)
    file = FileField(
        upload_to="resources/",
        validators=[validate_file_extension, validate_file_size],
    )
    resource_type = CharField(max_length=20, choices=ResourceType.choices)
    subject = ForeignKey(Subject, on_delete=CASCADE, related_name="resources")
    uploader = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="resources",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title
