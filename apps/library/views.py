from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ResourceForm
from .models import Resource, Subject


def _active_resources() -> QuerySet[Resource]:
    """Resources that are not soft-deleted."""
    return Resource.objects.filter(deleted_at__isnull=True)


def _get_owned_resource(request: HttpRequest, pk: int) -> Resource:
    """Return the resource only if the current user uploaded it."""
    resource = get_object_or_404(_active_resources(), pk=pk)
    if resource.uploader != request.user:
        raise PermissionDenied
    return resource


def resource_list(request: HttpRequest) -> HttpResponse:
    resources = _active_resources().select_related("subject", "uploader")

    query = request.GET.get("q", "").strip()
    subject_id = request.GET.get("subject", "")
    resource_type = request.GET.get("type", "")

    if query:
        resources = resources.filter(title__icontains=query)
    if subject_id.isdigit():
        resources = resources.filter(subject_id=int(subject_id))
    if resource_type:
        resources = resources.filter(resource_type=resource_type)

    context = {
        "resources": resources,
        "subjects": Subject.objects.filter(deleted_at__isnull=True),
        "resource_types": Resource.ResourceType.choices,
        "query": query,
        "selected_subject": subject_id,
        "selected_type": resource_type,
    }
    return render(request, "library/resource_list.html", context)


def resource_detail(request: HttpRequest, pk: int) -> HttpResponse:
    resource = get_object_or_404(_active_resources(), pk=pk)
    return render(request, "library/resource_detail.html", {"resource": resource})


@login_required
def resource_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploader = request.user
            resource.save()
            messages.success(request, "Resource uploaded.")
            return redirect("library:resource_detail", pk=resource.pk)
    else:
        form = ResourceForm()
    context = {"form": form, "page_title": "Upload resource"}
    return render(request, "library/resource_form.html", context)


@login_required
def resource_update(request: HttpRequest, pk: int) -> HttpResponse:
    resource = _get_owned_resource(request, pk)
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource updated.")
            return redirect("library:resource_detail", pk=resource.pk)
    else:
        form = ResourceForm(instance=resource)
    context = {"form": form, "page_title": "Edit resource"}
    return render(request, "library/resource_form.html", context)


@login_required
def resource_delete(request: HttpRequest, pk: int) -> HttpResponse:
    resource = _get_owned_resource(request, pk)
    if request.method == "POST":
        resource.soft_delete()
        messages.success(request, "Resource deleted.")
        return redirect("library:list")
    return render(request, "library/resource_confirm_delete.html", {"resource": resource})


@login_required
def resource_download(request: HttpRequest, pk: int) -> FileResponse:
    resource = get_object_or_404(_active_resources(), pk=pk)
    try:
        file_handle = resource.file.open("rb")
    except FileNotFoundError:
        raise Http404("File not found.")
    return FileResponse(file_handle, as_attachment=True)
