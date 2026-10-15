from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Event, EventRegistration


def lock_event(pk: int) -> Event:
    """Call inside atomic(). Lock the parent before reading registrations.

    The no-op UPDATE takes SQLite's write lock before any reads, avoiding
    read-to-write lock upgrades. PostgreSQL locks only this event row.
    All app mutations use the same order.
    """
    Event.objects.filter(pk=pk, deleted_at__isnull=True).update(updated_at=F("updated_at"))
    return get_object_or_404(Event.objects.select_for_update(), pk=pk, deleted_at__isnull=True)


@transaction.atomic
def register_student(event_id: int, student_id: int) -> EventRegistration:
    event = lock_event(event_id)
    registration = EventRegistration.objects.filter(event=event, student_id=student_id).first()
    if registration is not None and registration.deleted_at is None:
        raise ValidationError("You are already registered for this event.")
    if event.has_started:
        raise ValidationError("Registration is closed because this event has started.")
    if event.available_spots == 0:
        raise ValidationError("This event is full.")
    if registration is None:
        return EventRegistration.objects.create(event=event, student_id=student_id)
    registration.deleted_at = None
    registration.registered_at = timezone.now()
    registration.save(update_fields=("deleted_at", "registered_at", "updated_at"))
    return registration


@transaction.atomic
def cancel_registration(event_id: int, student_id: int) -> bool:
    event = lock_event(event_id)
    registration = EventRegistration.objects.filter(
        event=event,
        student_id=student_id,
        deleted_at__isnull=True,
    ).first()
    if registration is None:
        return False
    registration.soft_delete()
    return True
