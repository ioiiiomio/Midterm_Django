from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import (
    IntegrityError,
    OperationalError,
    close_old_connections,
    connection,
    transaction,
)
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from apps.events.forms import EventForm
from apps.events.models import Event, EventRegistration
from apps.events.services import cancel_registration, register_student


class EventsTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:  # noqa: N802
        user_model = get_user_model()
        cls.owner = user_model.objects.create_user(
            email="owner@kbtu.kz",
            first_name="Event",
            last_name="Owner",
        )
        cls.student = user_model.objects.create_user(
            email="student@kbtu.kz",
            first_name="Test",
            last_name="Student",
        )
        cls.admin = user_model.objects.create_user(email="admin@kbtu.kz", role="admin")
        cls.event = Event.objects.create(
            title="Campus cleanup",
            description="Help our campus",
            location="Main hall",
            date=timezone.now() + timedelta(days=7),
            category=Event.Category.VOLUNTEERING,
            organizer=cls.owner,
            capacity=2,
        )

    def url(self, name: str) -> str:
        return reverse(f"events:{name}", args=[self.event.pk])

    def data(self, **changes: object) -> dict:
        data = {
            "title": "New event",
            "description": "Event description",
            "location": "Room 42",
            "date": timezone.localtime(self.event.date).strftime("%Y-%m-%dT%H:%M"),
            "category": Event.Category.ACADEMIC,
            "capacity": 5,
        }
        data.update(changes)
        return data

    def test_public_list_and_detail(self) -> None:
        for url in [reverse("events:list"), self.url("detail")]:
            self.assertContains(self.client.get(url), self.event.title)

    def test_filters(self) -> None:
        url = reverse("events:list")
        day = timezone.localdate(self.event.date).isoformat()
        self.assertContains(self.client.get(url, {"date": day}), self.event.title)
        self.assertNotContains(self.client.get(url, {"date": "2000-01-01"}), self.event.title)
        self.assertContains(self.client.get(url, {"category": "volunteering"}), self.event.title)
        self.assertNotContains(self.client.get(url, {"category": "academic"}), self.event.title)
        self.assertContains(
            self.client.get(url, {"date": day, "category": "volunteering"}), self.event.title
        )
        self.assertNotContains(
            self.client.get(url, {"date": day, "category": "academic"}), self.event.title
        )

    def test_invalid_filters_display_errors(self) -> None:
        for params in [{"date": "bad"}, {"category": "bad"}]:
            response = self.client.get(reverse("events:list"), params)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["filter_form"].errors)

    def test_create_and_server_assigned_organizer(self) -> None:
        self.client.force_login(self.student)
        response = self.client.post(reverse("events:create"), self.data(organizer=self.owner.pk))
        created = Event.objects.get(title="New event")
        self.assertRedirects(response, created.get_absolute_url())
        self.assertEqual(created.organizer, self.student)

    def test_owner_edits_event(self) -> None:
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url("update")).status_code, 200)
        self.assertRedirects(self.client.post(self.url("update"), self.data()), self.url("detail"))
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "New event")
        self.assertEqual(self.event.organizer, self.owner)

    def test_delete_confirmation_then_soft_delete(self) -> None:
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url("delete")).status_code, 200)
        self.event.refresh_from_db()
        self.assertIsNone(self.event.deleted_at)
        self.assertRedirects(self.client.post(self.url("delete")), reverse("events:list"))
        self.event.refresh_from_db()
        self.assertIsNotNone(self.event.deleted_at)
        self.assertEqual(self.client.get(self.url("detail")).status_code, 404)
        self.assertNotContains(self.client.get(reverse("events:list")), self.event.title)

    def test_other_user_cannot_edit_or_delete(self) -> None:
        self.client.force_login(self.student)
        for action in ["update", "delete"]:
            self.assertEqual(self.client.get(self.url(action)).status_code, 403)
            self.assertEqual(self.client.post(self.url(action), self.data()).status_code, 403)

    def test_admin_can_manage(self) -> None:
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.url("update"), self.data()).status_code, 302)
        self.assertEqual(self.client.post(self.url("delete")).status_code, 302)

    def test_staff_alone_does_not_grant_ownership(self) -> None:
        self.student.is_staff = True
        self.student.save()
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(self.url("delete")).status_code, 403)

    def test_mutations_require_login(self) -> None:
        urls = [reverse("events:create")] + [
            self.url(name) for name in ["update", "delete", "register", "cancel"]
        ]
        for url in urls:
            response = self.client.post(url, self.data())
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse("users:login")))
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(EventRegistration.objects.count(), 0)

    def test_get_cannot_register_or_cancel(self) -> None:
        self.client.force_login(self.student)
        for action in ["register", "cancel"]:
            self.assertEqual(self.client.get(self.url(action)).status_code, 405)

    def test_csrf_required(self) -> None:
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.student)
        for action in ["register", "cancel", "update", "delete"]:
            self.assertEqual(client.post(self.url(action)).status_code, 403)

    def test_registration_and_participants(self) -> None:
        self.client.force_login(self.student)
        self.assertRedirects(self.client.post(self.url("register")), self.url("detail"))
        self.assertEqual(self.event.available_spots, 1)
        response = self.client.get(self.url("detail"))
        self.assertContains(response, "Test Student")
        self.assertContains(response, "Cancel my registration")
        registration = EventRegistration.objects.get()
        self.assertEqual(registration.student, self.student)
        self.assertIsNotNone(registration.registered_at)

    def test_duplicate_registration_message(self) -> None:
        self.client.force_login(self.student)
        self.client.post(self.url("register"))
        response = self.client.post(self.url("register"), follow=True)
        self.assertContains(response, "already registered")
        self.assertEqual(self.event.registration_count, 1)

    def test_duplicate_database_constraint(self) -> None:
        register_student(self.event.pk, self.student.pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            EventRegistration.objects.create(event=self.event, student=self.student)

    def test_full_event(self) -> None:
        self.event.capacity = 1
        self.event.save()
        register_student(self.event.pk, self.owner.pk)
        self.client.force_login(self.student)
        response = self.client.post(self.url("register"), follow=True)
        self.assertContains(response, "This event is full")
        self.assertEqual(self.event.registration_count, 1)
        self.assertEqual(self.event.available_spots, 0)

    def test_cancel_only_own_registration_and_rejoin(self) -> None:
        register_student(self.event.pk, self.owner.pk)
        registration = register_student(self.event.pk, self.student.pk)
        self.client.force_login(self.student)
        self.client.post(self.url("cancel"), {"student": self.owner.pk})
        self.assertEqual(self.event.registration_count, 1)
        self.assertTrue(
            self.event.registrations.filter(student=self.owner, deleted_at=None).exists()
        )
        registration.refresh_from_db()
        self.assertIsNotNone(registration.deleted_at)
        self.assertFalse(
            self.client.get(self.url("detail"))
            .context["participants"]
            .filter(
                student=self.student,
            )
            .exists()
        )
        self.client.post(self.url("register"))
        self.assertEqual(self.event.registration_count, 2)
        self.assertEqual(
            EventRegistration.objects.filter(student=self.student).get().pk, registration.pk
        )

    def test_cancelling_without_registration_is_safe(self) -> None:
        self.client.force_login(self.student)
        response = self.client.post(self.url("cancel"), follow=True)
        self.assertContains(response, "not registered")

    def test_service_cancellation_frees_place_for_another_student(self) -> None:
        self.event.capacity = 1
        self.event.save()
        register_student(self.event.pk, self.student.pk)
        self.assertTrue(cancel_registration(self.event.pk, self.student.pk))
        register_student(self.event.pk, self.owner.pk)
        self.assertEqual(self.event.registration_count, 1)

    def test_superuser_can_manage(self) -> None:
        self.student.is_superuser = True
        self.student.save()
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(self.url("update"), self.data()).status_code, 302)

    def test_admin_pages_and_registration_controls(self) -> None:
        self.admin.is_staff = True
        self.admin.is_superuser = True
        self.admin.save()
        self.client.force_login(self.admin)
        for model in ["event", "eventregistration"]:
            self.assertEqual(
                self.client.get(reverse(f"admin:events_{model}_changelist")).status_code, 200
            )
        self.assertEqual(self.client.get(reverse("admin:events_event_add")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("admin:events_eventregistration_add")).status_code, 403
        )
        response = self.client.post(
            reverse("admin:events_event_change", args=[self.event.pk]),
            self.data(capacity=3),
        )
        self.assertEqual(
            response.status_code,
            302,
            response.context["adminform"].form.errors if response.context else "",
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.capacity, 3)
        register_student(self.event.pk, self.student.pk)
        register_student(self.event.pk, self.owner.pk)
        response = self.client.post(
            reverse("admin:events_event_change", args=[self.event.pk]),
            self.data(capacity=1),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Capacity cannot be below")

    def test_started_event_registration_closed(self) -> None:
        Event.objects.filter(pk=self.event.pk).update(date=timezone.now() - timedelta(days=1))
        with self.assertRaisesMessage(ValidationError, "has started"):
            register_student(self.event.pk, self.student.pk)
        self.assertEqual(self.event.registration_count, 0)

    def test_deleted_event_actions_return_404(self) -> None:
        self.event.soft_delete()
        self.client.force_login(self.owner)
        for action in ["detail", "update", "delete", "register", "cancel"]:
            self.assertEqual(self.client.post(self.url(action), self.data()).status_code, 404)

    def test_missing_event_returns_404(self) -> None:
        self.assertEqual(self.client.get(reverse("events:detail", args=[99999])).status_code, 404)

    def test_form_validation(self) -> None:
        invalid = [
            {"date": timezone.now() - timedelta(days=1)},
            {"date": "bad"},
            {"capacity": 0},
            {"capacity": -1},
            {"category": "bad"},
            {"title": ""},
            {"location": ""},
            {"description": ""},
        ]
        for changes in invalid:
            with self.subTest(changes=changes):
                self.assertFalse(EventForm(data=self.data(**changes)).is_valid())
        self.assertTrue(EventForm(data=self.data()).is_valid())

    def test_unchanged_past_date_can_be_corrected(self) -> None:
        Event.objects.filter(pk=self.event.pk).update(date=timezone.now() - timedelta(days=1))
        self.event.refresh_from_db()
        self.client.force_login(self.owner)
        response = self.client.post(self.url("update"), self.data(location="New hall"))
        self.assertEqual(response.status_code, 302)
        original_date = self.event.date
        self.event.refresh_from_db()
        self.assertEqual(self.event.location, "New hall")
        self.assertEqual(self.event.date, original_date)

    def test_invalid_create_does_not_save(self) -> None:
        self.client.force_login(self.student)
        response = self.client.post(reverse("events:create"), self.data(capacity=0))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Event.objects.count(), 1)

    def test_capacity_cannot_shrink_below_participants(self) -> None:
        register_student(self.event.pk, self.owner.pk)
        register_student(self.event.pk, self.student.pk)
        self.client.force_login(self.owner)
        response = self.client.post(self.url("update"), self.data(capacity=1))
        self.assertEqual(response.status_code, 200)
        self.assertIn("capacity", response.context["form"].errors)
        self.event.refresh_from_db()
        self.assertEqual(self.event.capacity, 2)

    def test_database_capacity_and_category_constraints(self) -> None:
        for changes in [{"capacity": 0}, {"category": "invalid"}]:
            with self.subTest(changes=changes):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Event.objects.filter(pk=self.event.pk).update(**changes)

    def test_model_relationships_and_strings(self) -> None:
        registration = register_student(self.event.pk, self.student.pk)
        self.assertIn(self.event, self.owner.organized_events.all())
        self.assertIn(registration, self.student.event_registrations.all())
        self.assertEqual(str(self.event), "Campus cleanup")
        self.assertIn("student@kbtu.kz", str(registration))
        self.event.delete()
        self.assertFalse(EventRegistration.objects.filter(pk=registration.pk).exists())

    def test_logged_in_home_navbar_integration(self) -> None:
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse("home")), 'href="/events/"')


class RegistrationConcurrencyTests(TransactionTestCase):
    def test_two_connections_compete_for_last_spot(self) -> None:
        user_model = get_user_model()
        users = [user_model.objects.create_user(email=f"race{i}@kbtu.kz") for i in range(2)]
        event = Event.objects.create(
            title="Last spot",
            description="Concurrency",
            location="Hall",
            date=timezone.now() + timedelta(days=1),
            category=Event.Category.CAMPUS,
            organizer=users[0],
            capacity=1,
        )
        barrier = Barrier(2)

        def register(student_id: int) -> str:
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                register_student(event.pk, student_id)
                return "registered"
            except ValidationError:
                return "full"
            except OperationalError as error:
                if connection.vendor == "sqlite" and "locked" in str(error).lower():
                    return "busy"
                raise
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(register, [user.pk for user in users]))
        self.assertEqual(outcomes.count("registered"), 1, outcomes)
        self.assertEqual(event.registration_count, 1)
        self.assertEqual(event.available_spots, 0)
