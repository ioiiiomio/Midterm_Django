import shutil
import tempfile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.users.models import User

from .models import Resource, Subject
from .validators import (
    MAX_FILE_SIZE,
    validate_file_extension,
    validate_file_size,
)


TEMP_MEDIA = tempfile.mkdtemp()
PASSWORD = "pass12345"


def tearDownModule() -> None:
    shutil.rmtree(TEMP_MEDIA, ignore_errors=True)


def make_file(name: str = "notes.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"some file content")


def make_user(email: str, role: str) -> User:
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        first_name=email.split("@")[0].capitalize(),
        last_name="User",
        role=role,
    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LibraryTestCase(TestCase):
    """Base class: one student, two tutors, one admin, a subject, a resource."""

    def setUp(self) -> None:
        self.student = make_user("student@kbtu.kz", User.Role.STUDENT)
        self.tutor_a = make_user("tutora@kbtu.kz", User.Role.TUTOR)
        self.tutor_b = make_user("tutorb@kbtu.kz", User.Role.TUTOR)
        self.admin = make_user("admin@kbtu.kz", User.Role.ADMIN)
        self.subject = Subject.objects.create(name="Linear Algebra")
        self.resource = Resource.objects.create(
            title="Matrix notes",
            description="Chapter 1",
            file=make_file(),
            resource_type=Resource.ResourceType.LECTURE_NOTES,
            subject=self.subject,
            uploader=self.tutor_a,
        )

    def form_data(self, **extra: object) -> dict[str, object]:
        data: dict[str, object] = {
            "title": "New resource",
            "description": "",
            "resource_type": Resource.ResourceType.TEXTBOOK,
            "subject": self.subject.pk,
            "file": make_file(),
        }
        data.update(extra)
        return data

    def assert_redirects_to_login(self, url: str, method: str = "get") -> None:
        response = getattr(self.client, method)(url)
        self.assertRedirects(
            response,
            f"{settings.LOGIN_URL}?next={url}",
            fetch_redirect_response=False,
        )


class ModelTests(LibraryTestCase):
    def test_subject_str(self) -> None:
        self.assertEqual(str(self.subject), "Linear Algebra")

    def test_resource_str(self) -> None:
        self.assertEqual(str(self.resource), "Matrix notes")

    def test_resource_linked_to_uploader(self) -> None:
        self.assertEqual(self.resource.uploader, self.tutor_a)
        self.assertIn(self.resource, self.tutor_a.resources.all())

    def test_soft_delete_sets_deleted_at(self) -> None:
        self.resource.soft_delete()
        self.resource.refresh_from_db()
        self.assertIsNotNone(self.resource.deleted_at)


class ValidatorTests(TestCase):
    def test_allowed_extension_passes(self) -> None:
        validate_file_extension(make_file("book.pdf"))

    def test_bad_extension_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            validate_file_extension(make_file("virus.exe"))

    def test_small_file_passes(self) -> None:
        validate_file_size(make_file())

    def test_big_file_rejected(self) -> None:
        big_file = SimpleUploadedFile("big.pdf", b"x" * (MAX_FILE_SIZE + 1))
        with self.assertRaises(ValidationError):
            validate_file_size(big_file)


class AnonymousTests(LibraryTestCase):
    """Not logged in: everything redirects to the login page."""

    def test_list_redirects(self) -> None:
        self.assert_redirects_to_login(reverse("library:list"))

    def test_detail_redirects(self) -> None:
        self.assert_redirects_to_login(
            reverse("library:detail", args=[self.resource.pk])
        )

    def test_download_redirects(self) -> None:
        self.assert_redirects_to_login(
            reverse("library:download", args=[self.resource.pk])
        )

    def test_create_redirects(self) -> None:
        self.assert_redirects_to_login(reverse("library:create"))

    def test_edit_redirects(self) -> None:
        self.assert_redirects_to_login(
            reverse("library:update", args=[self.resource.pk])
        )

    def test_delete_redirects(self) -> None:
        self.assert_redirects_to_login(
            reverse("library:delete", args=[self.resource.pk]),
            method="post",
        )


class ListViewTests(LibraryTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.force_login(self.student)

    def test_list_page_opens(self) -> None:
        response = self.client.get(reverse("library:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Matrix notes")

    def test_search_by_title(self) -> None:
        url = reverse("library:list")
        found = self.client.get(url, {"q": "matrix"})
        missing = self.client.get(url, {"q": "chemistry"})
        self.assertContains(found, "Matrix notes")
        self.assertNotContains(missing, "Matrix notes")

    def test_filter_by_subject(self) -> None:
        other_subject = Subject.objects.create(name="Physics")
        response = self.client.get(
            reverse("library:list"), {"subject": other_subject.pk}
        )
        self.assertNotContains(response, "Matrix notes")

    def test_filter_by_type(self) -> None:
        response = self.client.get(reverse("library:list"), {"type": "textbook"})
        self.assertNotContains(response, "Matrix notes")

    def test_deleted_resource_is_hidden(self) -> None:
        self.resource.soft_delete()
        response = self.client.get(reverse("library:list"))
        self.assertNotContains(response, "Matrix notes")


class StudentTests(LibraryTestCase):
    """Student can see and download, but cannot add, edit or delete."""

    def setUp(self) -> None:
        super().setUp()
        self.client.force_login(self.student)

    def test_can_open_detail(self) -> None:
        response = self.client.get(reverse("library:detail", args=[self.resource.pk]))
        self.assertEqual(response.status_code, 200)

    def test_can_download(self) -> None:
        url = reverse("library:download", args=[self.resource.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = b"".join(response.streaming_content)
        self.assertEqual(content, b"some file content")

    def test_cannot_open_add_page(self) -> None:
        response = self.client.get(reverse("library:create"))
        self.assertEqual(response.status_code, 403)

    def test_cannot_post_add(self) -> None:
        response = self.client.post(reverse("library:create"), self.form_data())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Resource.objects.filter(title="New resource").exists())

    def test_cannot_edit(self) -> None:
        url = reverse("library:update", args=[self.resource.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_cannot_delete(self) -> None:
        url = reverse("library:delete", args=[self.resource.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.resource.refresh_from_db()
        self.assertIsNone(self.resource.deleted_at)

    def test_buttons_are_hidden(self) -> None:
        response = self.client.get(reverse("library:detail", args=[self.resource.pk]))
        self.assertNotContains(
            response, reverse("library:update", args=[self.resource.pk])
        )
        self.assertNotContains(
            response, reverse("library:delete", args=[self.resource.pk])
        )
        list_response = self.client.get(reverse("library:list"))
        self.assertNotContains(list_response, reverse("library:create"))


class TutorTests(LibraryTestCase):
    def test_tutor_can_add_and_becomes_owner(self) -> None:
        self.client.force_login(self.tutor_a)
        response = self.client.post(reverse("library:create"), self.form_data())
        self.assertEqual(response.status_code, 302)
        new = Resource.objects.get(title="New resource")
        self.assertEqual(new.uploader, self.tutor_a)

    def test_add_rejects_bad_file_type(self) -> None:
        self.client.force_login(self.tutor_a)
        data = self.form_data(file=make_file("virus.exe"))
        response = self.client.post(reverse("library:create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Resource.objects.filter(title="New resource").exists())

    def test_owner_can_edit(self) -> None:
        self.client.force_login(self.tutor_a)
        url = reverse("library:update", args=[self.resource.pk])
        response = self.client.post(url, self.form_data(title="Changed"))
        self.assertEqual(response.status_code, 302)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.title, "Changed")

    def test_owner_can_delete(self) -> None:
        self.client.force_login(self.tutor_a)
        url = reverse("library:delete", args=[self.resource.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.resource.refresh_from_db()
        self.assertIsNotNone(self.resource.deleted_at)

    def test_other_tutor_cannot_edit(self) -> None:
        self.client.force_login(self.tutor_b)
        url = reverse("library:update", args=[self.resource.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.post(url, self.form_data(title="Hacked")).status_code, 404
        )
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.title, "Matrix notes")

    def test_other_tutor_cannot_delete(self) -> None:
        self.client.force_login(self.tutor_b)
        url = reverse("library:delete", args=[self.resource.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.resource.refresh_from_db()
        self.assertIsNone(self.resource.deleted_at)

    def test_other_tutor_can_download(self) -> None:
        self.client.force_login(self.tutor_b)
        url = reverse("library:download", args=[self.resource.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_other_tutor_does_not_see_edit_buttons(self) -> None:
        self.client.force_login(self.tutor_b)
        response = self.client.get(reverse("library:detail", args=[self.resource.pk]))
        self.assertNotContains(
            response, reverse("library:update", args=[self.resource.pk])
        )

    def test_owner_sees_edit_buttons(self) -> None:
        self.client.force_login(self.tutor_a)
        response = self.client.get(reverse("library:detail", args=[self.resource.pk]))
        self.assertContains(
            response, reverse("library:update", args=[self.resource.pk])
        )


class AdminTests(LibraryTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.force_login(self.admin)

    def test_admin_can_add(self) -> None:
        response = self.client.post(reverse("library:create"), self.form_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Resource.objects.get(title="New resource").uploader, self.admin
        )

    def test_admin_can_edit_any_resource(self) -> None:
        url = reverse("library:update", args=[self.resource.pk])
        response = self.client.post(url, self.form_data(title="Admin edit"))
        self.assertEqual(response.status_code, 302)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.title, "Admin edit")

    def test_admin_can_delete_any_resource(self) -> None:
        url = reverse("library:delete", args=[self.resource.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.resource.refresh_from_db()
        self.assertIsNotNone(self.resource.deleted_at)


class SoftDeleteTests(LibraryTestCase):
    def test_deleted_resource_returns_404(self) -> None:
        self.resource.soft_delete()
        self.client.force_login(self.student)
        detail = reverse("library:detail", args=[self.resource.pk])
        download = reverse("library:download", args=[self.resource.pk])
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.get(download).status_code, 404)

    def test_deleted_resource_still_in_database(self) -> None:
        self.resource.soft_delete()
        self.assertTrue(Resource.objects.filter(pk=self.resource.pk).exists())
