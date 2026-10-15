from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, Count, Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.tutoring.forms import ReviewForm, TutoringSessionForm, TutorProfileForm
from apps.tutoring.models import Booking, Review, Subject, TutoringSession, TutorProfile
from apps.users.models import User


class TutorRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.is_authenticated and self.request.user.role == User.Role.TUTOR


class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.is_authenticated and self.request.user.role == User.Role.STUDENT


class TutorListView(ListView):
    model = TutorProfile
    template_name = "tutoring/tutor_list.html"
    context_object_name = "tutors"

    def get_queryset(self) -> QuerySet[TutorProfile]:
        queryset = (
            TutorProfile.objects.filter(
                deleted_at__isnull=True,
                is_available=True,
                user__is_active=True,
            )
            .select_related("user")
            .prefetch_related("subjects")
        )
        subject_id = self.request.GET.get("subject", "")
        if subject_id.isdigit():
            queryset = queryset.filter(subjects__pk=subject_id)
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(headline__icontains=search)
                | Q(bio__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        return queryset.distinct()

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        context["subjects"] = Subject.objects.filter(deleted_at__isnull=True)
        context["selected_subject"] = self.request.GET.get("subject", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class TutorDetailView(DetailView):
    model = TutorProfile
    template_name = "tutoring/tutor_detail.html"
    context_object_name = "tutor"

    def get_queryset(self) -> QuerySet[TutorProfile]:
        queryset = (
            TutorProfile.objects.filter(
                deleted_at__isnull=True,
                user__is_active=True,
            )
            .select_related("user")
            .prefetch_related("subjects")
        )
        if self.request.user.is_authenticated:
            return queryset.filter(Q(is_available=True) | Q(user=self.request.user))
        return queryset.filter(is_available=True)

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        context["sessions"] = (
            self.object.sessions.filter(
                deleted_at__isnull=True,
                is_cancelled=False,
                starts_at__gt=timezone.now(),
            )
            .select_related("subject")
            .annotate(
                confirmed_booking_count=Count(
                    "bookings",
                    filter=Q(bookings__status=Booking.Status.CONFIRMED),
                ),
            )
        )
        context["reviews"] = Review.objects.filter(
            booking__session__tutor=self.object,
        ).select_related("booking__student", "booking__session")
        context["average_rating"] = context["reviews"].aggregate(value=Avg("rating"))["value"]
        return context


class TutorProfileEditView(LoginRequiredMixin, TutorRequiredMixin, UpdateView):
    form_class = TutorProfileForm
    template_name = "tutoring/profile_form.html"
    success_url = reverse_lazy("tutoring:profile_edit")

    def get_object(self, queryset: QuerySet | None = None) -> TutorProfile:
        profile, _ = TutorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"headline": "", "hourly_rate": 0, "is_available": False},
        )
        return profile

    def form_valid(self, form: TutorProfileForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, "Your tutor profile has been updated.")
        return response


class MyScheduleView(LoginRequiredMixin, TutorRequiredMixin, ListView):
    model = TutoringSession
    template_name = "tutoring/my_schedule.html"
    context_object_name = "sessions"

    def get_queryset(self) -> QuerySet[TutoringSession]:
        return (
            TutoringSession.objects.filter(
                tutor__user=self.request.user,
                deleted_at__isnull=True,
                starts_at__gte=timezone.now(),
            )
            .select_related("subject")
            .prefetch_related("bookings__student")
            .annotate(
                confirmed_booking_count=Count(
                    "bookings",
                    filter=Q(bookings__status=Booking.Status.CONFIRMED),
                ),
            )
        )


class TutoringSessionCreateView(LoginRequiredMixin, TutorRequiredMixin, CreateView):
    model = TutoringSession
    form_class = TutoringSessionForm
    template_name = "tutoring/session_form.html"
    success_url = reverse_lazy("tutoring:my_schedule")

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        TutorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"headline": "", "hourly_rate": 0, "is_available": False},
        )
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: TutoringSessionForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, "Tutoring session added to your schedule.")
        return response


class TutoringSessionUpdateView(LoginRequiredMixin, TutorRequiredMixin, UpdateView):
    model = TutoringSession
    form_class = TutoringSessionForm
    template_name = "tutoring/session_form.html"
    success_url = reverse_lazy("tutoring:my_schedule")

    def get_queryset(self) -> QuerySet[TutoringSession]:
        return TutoringSession.objects.filter(
            tutor__user=self.request.user,
            deleted_at__isnull=True,
            is_cancelled=False,
            starts_at__gt=timezone.now(),
        )

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: TutoringSessionForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, "Tutoring session updated.")
        return response


class TutoringSessionCancelView(LoginRequiredMixin, TutorRequiredMixin, View):
    @transaction.atomic
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = get_object_or_404(
            TutoringSession.objects.select_for_update(),
            pk=pk,
            tutor__user=request.user,
            deleted_at__isnull=True,
            is_cancelled=False,
        )
        if session.starts_at <= timezone.now():
            messages.error(request, "Sessions that have already started cannot be cancelled.")
        else:
            session.is_cancelled = True
            session.save(update_fields=("is_cancelled", "updated_at"))
            session.bookings.filter(status=Booking.Status.CONFIRMED).update(
                status=Booking.Status.CANCELLED,
                updated_at=timezone.now(),
            )
            messages.success(request, "The session and its bookings have been cancelled.")
        return redirect("tutoring:my_schedule")


class MyBookingsView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = Booking
    template_name = "tutoring/my_bookings.html"
    context_object_name = "bookings"

    def get_queryset(self) -> QuerySet[Booking]:
        return Booking.objects.filter(student=self.request.user).select_related(
            "session__subject",
            "session__tutor__user",
        )

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context


class BookingCreateView(LoginRequiredMixin, StudentRequiredMixin, View):
    @transaction.atomic
    def post(self, request: HttpRequest, session_id: int) -> HttpResponse:
        session = get_object_or_404(
            TutoringSession.objects.select_for_update().select_related("tutor__user"),
            pk=session_id,
            deleted_at__isnull=True,
        )
        booking = Booking.objects.filter(student=request.user, session=session).first()
        if booking and booking.status == Booking.Status.CONFIRMED:
            messages.info(request, "You already have a booking for this session.")
        else:
            if booking is None:
                booking = Booking(student=request.user, session=session)
            else:
                booking.status = Booking.Status.CONFIRMED
            try:
                booking.full_clean()
                booking.save()
            except ValidationError as error:
                for message in error.messages:
                    messages.error(request, message)
            else:
                messages.success(request, "Your tutoring session is booked.")
        return redirect("tutoring:tutor_detail", pk=session.tutor_id)


class BookingCancelView(LoginRequiredMixin, StudentRequiredMixin, View):
    @transaction.atomic
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        booking = get_object_or_404(
            Booking.objects.select_for_update().select_related("session"),
            pk=pk,
            student=request.user,
            status=Booking.Status.CONFIRMED,
        )
        if booking.session.starts_at <= timezone.now():
            messages.error(request, "A booking cannot be cancelled after the session starts.")
        else:
            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=("status", "updated_at"))
            messages.success(request, "Your booking has been cancelled.")
        return redirect("tutoring:my_bookings")


class ReviewCreateView(LoginRequiredMixin, StudentRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = "tutoring/review_form.html"

    def get_booking(self) -> Booking:
        return get_object_or_404(
            Booking.objects.select_related("session__tutor"),
            pk=self.kwargs["booking_id"],
            student=self.request.user,
            status=Booking.Status.CONFIRMED,
            session__ends_at__lte=timezone.now(),
        )

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        context["booking"] = self.get_booking()
        return context

    def form_valid(self, form: ReviewForm) -> HttpResponse:
        booking = self.get_booking()
        if Review.objects.filter(booking=booking).exists():
            messages.info(self.request, "You have already reviewed this session.")
            return redirect("tutoring:my_bookings")
        form.instance.booking = booking
        try:
            form.instance.full_clean()
        except ValidationError as error:
            for message in error.messages:
                form.add_error(None, message)
            return self.form_invalid(form)
        response = super().form_valid(form)
        messages.success(self.request, "Your review has been submitted.")
        return response

    def get_success_url(self) -> str:
        return reverse("tutoring:tutor_detail", kwargs={"pk": self.get_booking().session.tutor_id})
