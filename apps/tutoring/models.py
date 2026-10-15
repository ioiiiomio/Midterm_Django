from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import (
    BooleanField,
    CharField,
    CheckConstraint,
    DateTimeField,
    DecimalField,
    ForeignKey,
    ManyToManyField,
    OneToOneField,
    PositiveSmallIntegerField,
    Q,
    TextChoices,
    TextField,
    UniqueConstraint,
)
from django.utils import timezone

from apps.abstracts.models import AbstractBaseModel
from apps.users.models import User


class Subject(AbstractBaseModel):
    name = CharField(max_length=100, unique=True)
    description = TextField(blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class TutorProfile(AbstractBaseModel):
    user = OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutor_profile",
    )
    headline = CharField(max_length=160)
    bio = TextField(blank=True)
    subjects = ManyToManyField(Subject, related_name="tutors")
    hourly_rate = DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=(MinValueValidator(0),),
    )
    years_experience = PositiveSmallIntegerField(default=0)
    is_available = BooleanField(default=True)

    class Meta:
        ordering = ("user__first_name", "user__last_name")

    def clean(self) -> None:
        if self.user_id and self.user.role != "tutor":
            raise ValidationError(
                {"user": "Only users with the tutor role can have a tutor profile."}
            )

    def __str__(self) -> str:
        return f"{self.user.full_name} - {self.headline}"


class TutoringSession(AbstractBaseModel):
    tutor = ForeignKey(TutorProfile, on_delete=models.PROTECT, related_name="sessions")
    subject = ForeignKey(Subject, on_delete=models.PROTECT, related_name="sessions")
    title = CharField(max_length=160)
    description = TextField(blank=True)
    starts_at = DateTimeField()
    ends_at = DateTimeField()
    location = CharField(max_length=200, blank=True)
    meeting_url = CharField(max_length=500, blank=True)
    capacity = PositiveSmallIntegerField(
        default=1,
        validators=(MinValueValidator(1),),
    )
    is_cancelled = BooleanField(default=False)

    class Meta:
        ordering = ("starts_at",)
        indexes = [models.Index(fields=("starts_at", "is_cancelled"))]
        constraints = [
            CheckConstraint(
                condition=Q(ends_at__gt=models.F("starts_at")),
                name="tutoring_session_end_after_start",
            ),
            CheckConstraint(
                condition=Q(capacity__gte=1),
                name="tutoring_session_capacity_positive",
            ),
        ]

    def clean(self) -> None:
        errors: dict[str, str] = {}
        if self.starts_at and self.starts_at <= timezone.now() and not self.is_cancelled:
            errors["starts_at"] = "A tutoring session must start in the future."
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            errors["ends_at"] = "The end time must be after the start time."
        if self.tutor_id and self.subject_id:
            if not self.tutor.subjects.filter(pk=self.subject_id).exists():
                errors["subject"] = "Choose a subject taught by this tutor."
        if self.tutor_id and self.starts_at and self.ends_at:
            conflicts = TutoringSession.objects.filter(
                tutor_id=self.tutor_id,
                is_cancelled=False,
                deleted_at__isnull=True,
                starts_at__lt=self.ends_at,
                ends_at__gt=self.starts_at,
            )
            if self.pk:
                conflicts = conflicts.exclude(pk=self.pk)
            if conflicts.exists():
                errors["starts_at"] = "This time overlaps another session on the tutor's schedule."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.title} ({self.starts_at:%Y-%m-%d %H:%M})"


class Booking(AbstractBaseModel):
    class Status(TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    student = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tutoring_bookings",
    )
    session = ForeignKey(TutoringSession, on_delete=models.PROTECT, related_name="bookings")
    status = CharField(max_length=10, choices=Status.choices, default=Status.CONFIRMED)

    class Meta:
        ordering = ("session__starts_at",)
        constraints = [
            UniqueConstraint(fields=("student", "session"), name="tutoring_unique_student_session"),
        ]

    def clean(self) -> None:
        if self.status != self.Status.CONFIRMED or not self.session_id or not self.student_id:
            return

        errors: dict[str, str] = {}
        session = self.session
        if self.student.role != "student":
            errors["student"] = "Only students can book tutoring sessions."
        if session.tutor.user_id == self.student_id:
            errors["student"] = "Tutors cannot book their own sessions."
        if session.is_cancelled or session.deleted_at is not None:
            errors["session"] = "This tutoring session is no longer available."
        if not session.tutor.is_available:
            errors["session"] = "This tutor is not accepting bookings right now."
        if session.starts_at <= timezone.now():
            errors["session"] = "Only future tutoring sessions can be booked."

        overlapping = Booking.objects.filter(
            student_id=self.student_id,
            status=self.Status.CONFIRMED,
            session__starts_at__lt=session.ends_at,
            session__ends_at__gt=session.starts_at,
            session__is_cancelled=False,
            session__deleted_at__isnull=True,
        ).exclude(session_id=session.pk)
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            errors["session"] = "You already have a booking that overlaps this time."

        seats_taken = Booking.objects.filter(
            session_id=session.pk,
            status=self.Status.CONFIRMED,
        )
        if self.pk:
            seats_taken = seats_taken.exclude(pk=self.pk)
        if seats_taken.count() >= session.capacity:
            errors["session"] = "This tutoring session is full."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.student} - {self.session} ({self.get_status_display()})"


class Review(AbstractBaseModel):
    booking = OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    rating = PositiveSmallIntegerField(validators=(MinValueValidator(1), MaxValueValidator(5)))
    comment = TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def student(self) -> User:
        return self.booking.student

    @property
    def tutor(self) -> TutorProfile:
        return self.booking.session.tutor

    def clean(self) -> None:
        if not self.booking_id:
            return
        if self.booking.status != Booking.Status.CONFIRMED:
            raise ValidationError(
                {"booking": "Only completed, confirmed sessions can be reviewed."}
            )
        if self.booking.session.ends_at > timezone.now():
            raise ValidationError({"booking": "A review can be submitted after the session ends."})
        if self.booking.student.role != "student":
            raise ValidationError({"booking": "Only students can review tutoring sessions."})

    def __str__(self) -> str:
        return f"{self.rating}/5 for {self.booking.session.tutor}"
