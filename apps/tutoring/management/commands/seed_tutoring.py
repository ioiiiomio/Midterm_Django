from argparse import ArgumentParser
from datetime import datetime, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.tutoring.models import Booking, Review, Subject, TutoringSession, TutorProfile
from apps.users.models import User


DEFAULT_DEMO_PASSWORD = "CampusHubDemo2026!"


class Command(BaseCommand):
    help = "Create local demo users and tutoring data."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--password",
            default=DEFAULT_DEMO_PASSWORD,
            help="Password assigned to all demo accounts (local development only).",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        password = options["password"]
        self._user(
            "demo.admin@example.com",
            "Demo",
            "Admin",
            User.Role.ADMIN,
            password,
            is_staff=True,
            is_superuser=True,
        )
        math_tutor_user = self._user(
            "demo.math.tutor@example.com",
            "Mira",
            "Sadykova",
            User.Role.TUTOR,
            password,
        )
        physics_tutor_user = self._user(
            "demo.physics.tutor@example.com",
            "Arman",
            "Kim",
            User.Role.TUTOR,
            password,
        )
        programming_tutor_user = self._user(
            "demo.programming.tutor@example.com",
            "Dana",
            "Lee",
            User.Role.TUTOR,
            password,
        )
        student = self._user(
            "demo.student@example.com",
            "Ayan",
            "Student",
            User.Role.STUDENT,
            password,
        )
        second_student = self._user(
            "demo.student2@example.com",
            "Sara",
            "Student",
            User.Role.STUDENT,
            password,
        )

        algebra, _ = Subject.objects.update_or_create(
            name="Algebra and Calculus",
            defaults={"description": "Foundations, calculus, and exam preparation."},
        )
        physics, _ = Subject.objects.update_or_create(
            name="Physics",
            defaults={"description": "Mechanics and introductory university physics."},
        )
        programming, _ = Subject.objects.update_or_create(
            name="Python Programming",
            defaults={"description": "Python fundamentals, Django, and project help."},
        )

        math_tutor = self._profile(
            math_tutor_user,
            "Patient calculus tutor",
            "Step-by-step explanations and exam practice.",
            "25.00",
            4,
            [algebra],
        )
        physics_tutor = self._profile(
            physics_tutor_user,
            "Physics made practical",
            "Mechanics, problem solving, and lab preparation.",
            "22.00",
            3,
            [physics],
        )
        programming_tutor = self._profile(
            programming_tutor_user,
            "Python and Django mentor",
            "Build confidence through small, working projects.",
            "30.00",
            5,
            [programming],
        )

        now = timezone.localtime()
        open_session = self._session(
            math_tutor,
            algebra,
            "Calculus clinic",
            now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=2),
            capacity=4,
            description="A small-group session covering derivatives and integrals.",
            location="Main Library, Room 204",
        )
        nearly_full_session = self._session(
            math_tutor,
            algebra,
            "Calculus exam preparation",
            now.replace(hour=13, minute=0, second=0, microsecond=0) + timedelta(days=3),
            capacity=2,
            description="Practice problems and a focused exam review.",
            location="Online",
            meeting_url="https://meet.example.com/demo-calculus",
        )
        self._session(
            physics_tutor,
            physics,
            "Mechanics problem-solving workshop",
            now.replace(hour=15, minute=0, second=0, microsecond=0) + timedelta(days=2),
            capacity=3,
            description="Work through forces, energy, and momentum problems.",
            location="Science Building, Room 118",
        )
        self._session(
            programming_tutor,
            programming,
            "Build your first Django app",
            now.replace(hour=11, minute=0, second=0, microsecond=0) + timedelta(days=4),
            capacity=3,
            description="A guided introduction to models, views, and URLs.",
            location="Online",
            meeting_url="https://meet.example.com/demo-django",
        )
        completed_session = self._session(
            math_tutor,
            algebra,
            "Introduction to integrals",
            now - timedelta(days=7),
            capacity=1,
            description="Completed demo session with a review.",
            location="Main Library, Room 204",
        )
        cancelled_session = self._session(
            physics_tutor,
            physics,
            "Cancelled mechanics session",
            now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=5),
            capacity=3,
            description="Demo of a cancelled session and its booking.",
            location="Science Building, Room 118",
            is_cancelled=True,
        )

        self._booking(student, open_session)
        self._booking(second_student, open_session)
        self._booking(student, nearly_full_session)
        self._booking(student, completed_session)
        completed_booking = Booking.objects.get(student=student, session=completed_session)
        Review.objects.update_or_create(
            booking=completed_booking,
            defaults={"rating": 5, "comment": "Clear explanations and useful practice."},
        )
        self._booking(second_student, cancelled_session, status=Booking.Status.CANCELLED)

        self.stdout.write(self.style.SUCCESS("Tutoring demo data is ready."))
        self.stdout.write(f"Demo password: {password}")
        self.stdout.write("Admin: demo.admin@example.com")
        self.stdout.write("Tutors: demo.math.tutor@example.com, demo.physics.tutor@example.com, ")
        self.stdout.write("        demo.programming.tutor@example.com")
        self.stdout.write("Students: demo.student@example.com, demo.student2@example.com")
        self.stdout.write(
            f"Created/updated 3 tutors, 3 subjects, 6 sessions, and "
            f"{Booking.objects.count()} total bookings."
        )

    @staticmethod
    def _user(
        email: str,
        first_name: str,
        last_name: str,
        role: str,
        password: str,
        *,
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> User:
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_active": True,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        user.set_password(password)
        user.save(update_fields=("password", "updated_at"))
        return user

    @staticmethod
    def _profile(
        user: User,
        headline: str,
        bio: str,
        hourly_rate: str,
        years_experience: int,
        subjects: list[Subject],
    ) -> TutorProfile:
        profile, _ = TutorProfile.objects.update_or_create(
            user=user,
            defaults={
                "headline": headline,
                "bio": bio,
                "hourly_rate": hourly_rate,
                "years_experience": years_experience,
                "is_available": True,
            },
        )
        profile.subjects.set(subjects)
        return profile

    @staticmethod
    def _session(
        tutor: TutorProfile,
        subject: Subject,
        title: str,
        starts_at: datetime,
        *,
        capacity: int,
        description: str,
        location: str,
        meeting_url: str = "",
        is_cancelled: bool = False,
    ) -> TutoringSession:
        session, _ = TutoringSession.objects.update_or_create(
            tutor=tutor,
            title=title,
            defaults={
                "subject": subject,
                "description": description,
                "starts_at": starts_at,
                "ends_at": starts_at + timedelta(hours=1),
                "capacity": capacity,
                "location": location,
                "meeting_url": meeting_url,
                "is_cancelled": is_cancelled,
            },
        )
        return session

    @staticmethod
    def _booking(
        student: User,
        session: TutoringSession,
        *,
        status: str = Booking.Status.CONFIRMED,
    ) -> Booking:
        booking, _ = Booking.objects.update_or_create(
            student=student,
            session=session,
            defaults={"status": status},
        )
        return booking
