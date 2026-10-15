from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.abstracts.models import AbstractBaseModel


class Event(AbstractBaseModel):
    """A campus activity owned by its organizer."""

    class Category(models.TextChoices):
        VOLUNTEERING = "volunteering", "Volunteering"
        HOLIDAYS = "holidays", "Holidays"
        ACADEMIC = "academic", "Academic Events"
        CAMPUS = "campus", "Campus Activities"

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ("date", "pk")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1), name="events_capacity_gte_1"
            ),
            models.CheckConstraint(
                condition=models.Q(category__in=["volunteering", "holidays", "academic", "campus"]),
                name="events_valid_category",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("events:detail", kwargs={"pk": self.pk})

    def clean(self) -> None:
        super().clean()
        previous = Event.objects.filter(pk=self.pk).first() if self.pk else None
        if self.date and (previous is None or self.date != previous.date):
            if self.date <= timezone.now():
                raise ValidationError({"date": "Choose a future date and time."})
        if self.pk and self.capacity is not None and self.capacity < self.registration_count:
            raise ValidationError({"capacity": "Capacity cannot be below the participant count."})

    @property
    def registration_count(self) -> int:
        return self.registrations.filter(deleted_at__isnull=True).count()

    @property
    def available_spots(self) -> int:
        return max(0, self.capacity - self.registration_count)

    @property
    def has_started(self) -> bool:
        return self.date <= timezone.now()


class EventRegistration(AbstractBaseModel):
    """One student's place; cancellation uses the shared soft-delete flag."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_registrations",
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("registered_at", "pk")
        constraints = [
            models.UniqueConstraint(fields=("event", "student"), name="events_unique_student"),
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.event}"
