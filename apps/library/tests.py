import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

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


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LibraryTestCase(TestCase):
    """Base class: creates two users, a subject and one resource."""

    def setUp(self) -> None:
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            email="owner@kbtu.kz",
            password=PASSWORD,
            first_name="Owner",
            last_name="User",
        )
        self.other = user_model.objects.create_user(
            email="other@kbtu.kz",
            password=PASSWORD,
            first_name="Other",
            last_name="User",
        )
        self.subject = Subject.objects.create(name="Linear Algebra")
        self.resource = Resource.objects.create(
            title="Matrix notes",
            description="Chapter 1",
            file=make_file(),
            resource_type=Resource.ResourceType.LECTURE_NOTES,
            subject=self.subject,
            uploader=self.owner,
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


class ModelTests(LibraryTestCase):
    def test_subject_str(self) -> None:
        self.assertEqual(str(self.subject), "Linear Algebra")

    def test_resource_str(self) -> None:
        self.assertEqual(str(self.resource), "Matrix notes")

    def test_resource_linked_to_uploader(self) -> None:
        self.assertEqual(self.resource.uploader, self.owner)
        self.assertIn(self.resource, self.owner.resources.all())

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


class ListViewTests(LibraryTestCase):
    def test_list_page_opens(self) -> None:
        response = self.client.get(reverse("library:resource_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Matrix notes")

    def test_search_by_title(self) -> None:
        url = reverse("library:resource_list")
        found = self.client.get(url, {"q": "matrix"})
        missing = self.client.get(url, {"q": "chemistry"})
        self.assertContains(found, "Matrix notes")
        self.assertNotContains(missing, "Matrix notes")

    def test_filter_by_subject(self) -> None:
        other_subject = Subject.objects.create(name="Physics")
        url = reverse("library:resource_list")
        response = self.client.get(url, {"subject": other_subject.pk})
        self.assertNotContains(response, "Matrix notes")

    def test_filter_by_type(self) -> None:
        url = reverse("library:resource_list")
        response = self.client.get(url, {"type": "textbook"})
        self.assertNotContains(response, "Matrix notes")

    def test_deleted_resource_is_hidden(self) -> None:
        self.resource.soft_delete()
        response = self.client.get(reverse("library:resource_list"))
        self.assertNotContains(response, "Matrix notes")


class CreateViewTests(LibraryTestCase):
    def test_create_requires_login(self) -> None:
        response = self.client.get(reverse("library:resource_create"))
        self.assertEqual(response.status_code, 302)

    def test_create_valid_resource(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.post(reverse("library:resource_create"), self.form_data())
        self.assertEqual(response.status_code, 302)
        new = Resource.objects.get(title="New resource")
        self.assertEqual(new.uploader, self.owner)

    def test_create_rejects_bad_file_type(self) -> None:
        self.client.force_login(self.owner)
        data = self.form_data(file=make_file("virus.exe"))
        response = self.client.post(reverse("library:resource_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Resource.objects.filter(title="New resource").exists())


class PermissionTests(LibraryTestCase):
    def test_owner_can_edit(self) -> None:
        self.client.force_login(self.owner)
        url = reverse("library:resource_update", args=[self.resource.pk])
        response = self.client.post(url, self.form_data(title="Changed"))
        self.assertEqual(response.status_code, 302)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.title, "Changed")

    def test_other_user_cannot_edit(self) -> None:
        self.client.force_login(self.other)
        url = reverse("library:resource_update", args=[self.resource.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_delete(self) -> None:
        self.client.force_login(self.other)
        url = reverse("library:resource_delete", args=[self.resource.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.resource.refresh_from_db()
        self.assertIsNone(self.resource.deleted_at)

    def test_owner_can_delete(self) -> None:
        self.client.force_login(self.owner)
        url = reverse("library:resource_delete", args=[self.resource.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.resource.refresh_from_db()
        self.assertIsNotNone(self.resource.deleted_at)


class DownloadTests(LibraryTestCase):
    def test_download_requires_login(self) -> None:
        url = reverse("library:resource_download", args=[self.resource.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_can_download(self) -> None:
        self.client.force_login(self.other)
        url = reverse("library:resource_download", args=[self.resource.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = b"".join(response.streaming_content)
        self.assertEqual(content, b"some file content")
