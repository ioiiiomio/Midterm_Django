from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet

from apps.users.models import User

from .models import Resource


class CanAddResourceMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only tutors and admins can add resources."""

    def test_func(self) -> bool:
        return self.request.user.role in (User.Role.TUTOR, User.Role.ADMIN)


class OwnResourceMixin(LoginRequiredMixin):
    """Tutors can change only their own resources, admins can change any."""

    def get_queryset(self) -> QuerySet[Resource]:
        resources = Resource.objects.filter(deleted_at__isnull=True)
        if self.request.user.role == User.Role.ADMIN:
            return resources
        return resources.filter(uploader=self.request.user)
