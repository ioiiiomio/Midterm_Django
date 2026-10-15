from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ClubForm
from .models import Club, Membership


def club_list(request: HttpRequest) -> HttpResponse:
    """All clubs with search by name/description and filter by category."""
    query = request.GET.get("q", "")
    category = request.GET.get("category", "")

    clubs = Club.objects.select_related("president").order_by("name")

    if query:
        clubs = clubs.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category:
        clubs = clubs.filter(category=category)

    return render(
        request,
        "clubs/club_list.html",
        {
            "clubs": clubs,
            "categories": Club.CATEGORY_CHOICES,
            "query": query,
            "category": category,
        },
    )


def club_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """One club: info, approved members, and pending requests for the president."""
    club = get_object_or_404(Club.objects.select_related("president"), pk=pk)
    members = club.memberships.filter(status="approved").select_related("user")
    pending_requests = (
        club.memberships.filter(status="pending").select_related("user")
        if request.user == club.president
        else None
    )

    user_membership = None
    if request.user.is_authenticated:
        user_membership = club.memberships.filter(user=request.user).first()

    return render(
        request,
        "clubs/club_detail.html",
        {
            "club": club,
            "members": members,
            "pending_requests": pending_requests,
            "user_membership": user_membership,
        },
    )


@login_required
def club_create(request: HttpRequest) -> HttpResponse:
    """Create a club. The creator becomes president and an approved member."""
    if request.method == "POST":
        form = ClubForm(request.POST, request.FILES)
        if form.is_valid():
            club = form.save(commit=False)
            club.president = request.user
            club.save()

            Membership.objects.create(club=club, user=request.user, status="approved")
            messages.success(request, "Club created successfully!")
            return redirect("clubs:detail", pk=club.pk)
    else:
        form = ClubForm()

    return render(
        request,
        "clubs/club_form.html",
        {"form": form, "title": "Create Club"},
    )


@login_required
def club_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a club. Only the president can do it."""
    club = get_object_or_404(Club, pk=pk)
    if request.user != club.president:
        messages.error(request, "You do not have the authority to edit club information")
        return redirect("clubs:detail", pk=club.pk)

    if request.method == "POST":
        form = ClubForm(request.POST, request.FILES, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, "Club information updated successfully!")
            return redirect("clubs:detail", pk=club.pk)
    else:
        form = ClubForm(instance=club)

    return render(
        request,
        "clubs/club_form.html",
        {"form": form, "title": "Edit Club", "club": club},
    )


@login_required
def club_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Confirm page on GET, delete on POST. Only the president can do it."""
    club = get_object_or_404(Club, pk=pk)
    if request.user != club.president:
        messages.error(request, "You do not have the authority to delete this club")
        return redirect("clubs:detail", pk=club.pk)

    if request.method == "POST":
        club.delete()
        messages.success(request, "Club deleted successfully")
        return redirect("clubs:list")

    return render(request, "clubs/club_confirm_delete.html", {"club": club})


@login_required
@require_POST
def join_request(request: HttpRequest, pk: int) -> HttpResponse:
    """Send a request to join a club."""
    club = get_object_or_404(Club, pk=pk)
    _, created = Membership.objects.get_or_create(club=club, user=request.user)
    if created:
        messages.success(request, "Membership request submitted successfully!")
    else:
        messages.info(request, "You have already requested or joined this club.")
    return redirect("clubs:detail", pk=club.pk)


@login_required
@require_POST
def manage_request(request: HttpRequest, membership_id: int, action: str) -> HttpResponse:
    """Approve or reject a join request. Only the club president can do it."""
    membership = get_object_or_404(Membership.objects.select_related("club"), id=membership_id)
    if request.user != membership.club.president:
        messages.error(request, "Permission denied")
        return redirect("clubs:detail", pk=membership.club.pk)

    if action == "approve":
        membership.status = "approved"
        messages.success(request, f"User {membership.user.email} accepted to the club.")
    elif action == "reject":
        membership.status = "rejected"
        messages.info(request, f"Request from {membership.user.email} rejected.")
    else:
        messages.error(request, "Unknown action")
        return redirect("clubs:detail", pk=membership.club.pk)

    membership.save()
    return redirect("clubs:detail", pk=membership.club.pk)