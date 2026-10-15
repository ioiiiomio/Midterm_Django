from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.tutoring.models import Booking, Review, Subject, TutoringSession, TutorProfile
from apps.users.models import User


class TutoringTests(TestCase):
    def setUp(self) -> None:
        self.student = User.objects.create_user(
            email="student@example.com",
            password="test-password-123",
            first_name="Student",
            last_name="One",
        )
        self.tutor_user = User.objects.create_user(
            email="tutor@example.com",
            password="test-password-123",
            first_name="Tutor",
            last_name="One",
            role=User.Role.TUTOR,
        )
        self.subject = Subject.objects.create(name="Mathematics")
        self.tutor = TutorProfile.objects.create(
            user=self.tutor_user,
            headline="Math tutor",
            hourly_rate=25,
        )
        self.tutor.subjects.add(self.subject)
        self.session = self.make_session()

    def make_session(
        self,
        *,
        tutor: TutorProfile | None = None,
        starts_at: datetime | None = None,
        capacity: int = 1,
    ) -> TutoringSession:
        starts_at = starts_at or timezone.now() + timedelta(days=2)
        return TutoringSession.objects.create(
            tutor=tutor or self.tutor,
            subject=self.subject,
            title="Algebra review",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            capacity=capacity,
        )

    def login(self, user: User) -> None:
        self.client.force_login(user)

    def test_tutor_directory_searches_and_filters_by_subject(self) -> None:
        response = self.client.get(reverse("tutoring:list"), {"subject": self.subject.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Math tutor")

    def test_only_tutors_can_edit_tutor_profile(self) -> None:
        self.login(self.student)

        response = self.client.get(reverse("tutoring:profile_edit"))

        self.assertEqual(response.status_code, 403)

    def test_tutor_can_manage_only_own_sessions(self) -> None:
        other_user = User.objects.create_user(
            email="other@example.com",
            password="test-password-123",
            first_name="Other",
            last_name="Tutor",
            role=User.Role.TUTOR,
        )
        other_profile = TutorProfile.objects.create(
            user=other_user,
            headline="Other tutor",
            hourly_rate=30,
        )
        other_profile.subjects.add(self.subject)
        other_session = self.make_session(tutor=other_profile)
        self.login(self.tutor_user)

        response = self.client.get(
            reverse("tutoring:session_edit", kwargs={"pk": other_session.pk}),
        )

        self.assertEqual(response.status_code, 404)

    def test_overlapping_tutor_sessions_fail_validation(self) -> None:
        conflicting = TutoringSession(
            tutor=self.tutor,
            subject=self.subject,
            title="Conflicting lesson",
            starts_at=self.session.starts_at + timedelta(minutes=30),
            ends_at=self.session.ends_at + timedelta(minutes=30),
            capacity=1,
        )

        with self.assertRaises(ValidationError):
            conflicting.full_clean()

    def test_booking_enforces_capacity_and_prevents_duplicate(self) -> None:
        self.login(self.student)
        url = reverse("tutoring:booking_create", kwargs={"session_id": self.session.pk})

        self.client.post(url)
        self.client.post(url)

        self.assertEqual(
            Booking.objects.filter(session=self.session, status=Booking.Status.CONFIRMED).count(),
            1,
        )

    def test_student_cannot_book_overlapping_sessions(self) -> None:
        other_user = User.objects.create_user(
            email="second-tutor@example.com",
            password="test-password-123",
            first_name="Second",
            last_name="Tutor",
            role=User.Role.TUTOR,
        )
        other_profile = TutorProfile.objects.create(
            user=other_user,
            headline="Second tutor",
            hourly_rate=30,
        )
        other_profile.subjects.add(self.subject)
        second_session = self.make_session(tutor=other_profile, starts_at=self.session.starts_at)
        self.login(self.student)
        self.client.post(reverse("tutoring:booking_create", kwargs={"session_id": self.session.pk}))

        self.client.post(
            reverse("tutoring:booking_create", kwargs={"session_id": second_session.pk})
        )

        self.assertEqual(
            Booking.objects.filter(student=self.student, status=Booking.Status.CONFIRMED).count(), 1
        )

    def test_cancelled_booking_can_be_rebooked_when_spot_is_open(self) -> None:
        self.login(self.student)
        self.client.post(reverse("tutoring:booking_create", kwargs={"session_id": self.session.pk}))
        booking = Booking.objects.get(student=self.student, session=self.session)
        self.client.post(reverse("tutoring:booking_cancel", kwargs={"pk": booking.pk}))
        self.client.post(reverse("tutoring:booking_create", kwargs={"session_id": self.session.pk}))

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_only_attending_student_can_review_completed_session(self) -> None:
        past_start = timezone.now() - timedelta(days=2)
        past_session = self.make_session(starts_at=past_start)
        booking = Booking.objects.create(student=self.student, session=past_session)
        self.login(self.student)

        response = self.client.post(
            reverse("tutoring:review_create", kwargs={"booking_id": booking.pk}),
            {"rating": 5, "comment": "Clear explanations."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(booking=booking, rating=5).exists())

    def test_review_cannot_be_submitted_before_session_ends(self) -> None:
        booking = Booking.objects.create(student=self.student, session=self.session)
        self.login(self.student)

        response = self.client.get(
            reverse("tutoring:review_create", kwargs={"booking_id": booking.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_tutor_cancellation_cancels_confirmed_bookings(self) -> None:
        Booking.objects.create(student=self.student, session=self.session)
        self.login(self.tutor_user)

        self.client.post(reverse("tutoring:session_cancel", kwargs={"pk": self.session.pk}))

        self.session.refresh_from_db()
        booking = Booking.objects.get(student=self.student, session=self.session)
        self.assertTrue(self.session.is_cancelled)
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
