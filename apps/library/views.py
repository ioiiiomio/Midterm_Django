from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import ResourceForm
from .mixins import CanAddResourceMixin, OwnResourceMixin
from .models import Resource, Subject


def _active_resources() -> QuerySet[Resource]:
    """Resources that are not soft-deleted."""
    return Resource.objects.filter(deleted_at__isnull=True)


class ResourceListView(LoginRequiredMixin, ListView):
    template_name = "library/resource_list.html"
    context_object_name = "resources"

    def get_queryset(self) -> QuerySet[Resource]:
        resources = _active_resources().select_related("subject", "uploader")

        query = self.request.GET.get("q", "").strip()
        subject_id = self.request.GET.get("subject", "")
        resource_type = self.request.GET.get("type", "")

        if query:
            resources = resources.filter(title__icontains=query)
        if subject_id.isdigit():
            resources = resources.filter(subject_id=int(subject_id))
        if resource_type:
            resources = resources.filter(resource_type=resource_type)
        return resources

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subjects": Subject.objects.filter(deleted_at__isnull=True),
                "resource_types": Resource.ResourceType.choices,
                "query": self.request.GET.get("q", "").strip(),
                "selected_subject": self.request.GET.get("subject", ""),
                "selected_type": self.request.GET.get("type", ""),
            }
        )
        return context


class ResourceDetailView(LoginRequiredMixin, DetailView):
    template_name = "library/resource_detail.html"
    context_object_name = "resource"

    def get_queryset(self) -> QuerySet[Resource]:
        return _active_resources().select_related("subject", "uploader")


class ResourceCreateView(CanAddResourceMixin, SuccessMessageMixin, CreateView):
    form_class = ResourceForm
    template_name = "library/resource_form.html"
    success_message = "Resource uploaded."
    extra_context = {"page_title": "Upload resource"}

    def form_valid(self, form: ResourceForm) -> HttpResponse:
        form.instance.uploader = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("library:detail", kwargs={"pk": self.object.pk})


class ResourceUpdateView(OwnResourceMixin, SuccessMessageMixin, UpdateView):
    form_class = ResourceForm
    template_name = "library/resource_form.html"
    success_message = "Resource updated."
    extra_context = {"page_title": "Edit resource"}

    def get_success_url(self) -> str:
        return reverse("library:detail", kwargs={"pk": self.object.pk})


class ResourceDeleteView(OwnResourceMixin, View):
    """POST-only soft delete."""

    http_method_names = ["post"]

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        resource = get_object_or_404(self.get_queryset(), pk=pk)
        resource.soft_delete()
        messages.success(request, "Resource deleted.")
        return redirect("library:list")


class ResourceDownloadView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int) -> FileResponse:
        resource = get_object_or_404(_active_resources(), pk=pk)
        try:
            file_handle = resource.file.open("rb")
        except FileNotFoundError:
            raise Http404("File not found.") from None
        return FileResponse(file_handle, as_attachment=True)
