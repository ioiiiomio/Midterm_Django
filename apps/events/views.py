from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import OperationalError, connection, transaction
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import EventFilterForm, EventForm
from .models import Event
from .services import cancel_registration, lock_event, register_student


def can_manage(request: HttpRequest, event: Event) -> bool:
    user = request.user
    return user.is_authenticated and (
        event.organizer_id == user.pk or user.is_superuser or user.role == "admin"
    )


def event_list(request: HttpRequest) -> HttpResponse:
    events = (
        Event.objects.filter(deleted_at__isnull=True)
        .select_related("organizer")
        .annotate(
            participant_count=Count(
                "registrations", filter=Q(registrations__deleted_at__isnull=True)
            ),
        )
    )
    form = EventFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data["date"]:
            events = events.filter(date__date=form.cleaned_data["date"])
        if form.cleaned_data["category"]:
            events = events.filter(category=form.cleaned_data["category"])
    else:
        events = events.none()
    return render(request, "events/event_list.html", {"events": events, "filter_form": form})


def event_detail(request: HttpRequest, pk: int) -> HttpResponse:
    event = get_object_or_404(
        Event.objects.select_related("organizer"), pk=pk, deleted_at__isnull=True
    )
    participants = event.registrations.filter(deleted_at__isnull=True).select_related("student")
    registered = (
        request.user.is_authenticated and participants.filter(student=request.user).exists()
    )
    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
            "participants": participants,
            "is_registered": registered,
            "can_manage": can_manage(request, event),
        },
    )


@login_required
def event_create(request: HttpRequest) -> HttpResponse:
    form = EventForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.organizer = request.user
        event.save()
        messages.success(request, "Event created.")
        return redirect(event)
    return render(request, "events/event_form.html", {"form": form, "page_title": "Create event"})


@login_required
def event_update(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        event = (
            lock_event(pk)
            if request.method == "POST"
            else get_object_or_404(
                Event,
                pk=pk,
                deleted_at__isnull=True,
            )
        )
        if not can_manage(request, event):
            raise PermissionDenied
        form = EventForm(request.POST if request.method == "POST" else None, instance=event)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "Event updated.")
            return redirect(event)
    return render(request, "events/event_form.html", {"form": form, "page_title": "Edit event"})


@login_required
def event_delete(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        event = (
            lock_event(pk)
            if request.method == "POST"
            else get_object_or_404(
                Event,
                pk=pk,
                deleted_at__isnull=True,
            )
        )
        if not can_manage(request, event):
            raise PermissionDenied
        if request.method == "POST":
            event.soft_delete()
            messages.success(request, "Event deleted.")
            return redirect("events:list")
    return render(request, "events/event_confirm_delete.html", {"event": event})


@login_required
@require_POST
def event_register(request: HttpRequest, pk: int) -> HttpResponse:
    try:
        register_student(pk, request.user.pk)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    except OperationalError as error:
        if connection.vendor != "sqlite" or "locked" not in str(error).lower():
            raise
        messages.error(request, "Registration is busy. Please try again.")
    else:
        messages.success(request, "You are registered for this event.")
    return redirect("events:detail", pk=pk)


@login_required
@require_POST
def event_cancel(request: HttpRequest, pk: int) -> HttpResponse:
    try:
        cancelled = cancel_registration(pk, request.user.pk)
    except OperationalError as error:
        if connection.vendor != "sqlite" or "locked" not in str(error).lower():
            raise
        messages.error(request, "Registration is busy. Please try again.")
    else:
        if cancelled:
            messages.success(request, "Your registration has been cancelled.")
        else:
            messages.info(request, "You are not registered for this event.")
    return redirect("events:detail", pk=pk)
