<<<<<<< HEAD
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
=======
>>>>>>> origin/main

from .forms import ClubForm
from .models import Club, Membership


# Club List
def club_list(request):
  query = request.GET.get('q', '')
  category = request.GET.get('category', '')

  clubs = Club.objects.all()

  if query:
    clubs = clubs.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )
  if category:
    clubs = clubs.filter(category=category)

  return render(
      request,
      'clubs/club_list.html',
      {
          'clubs': clubs,
          'categories': Club.CATEGORY_CHOICES,
          'query': query,
      },
  )


# Club Detail
def club_detail(request, pk):
  club = get_object_or_404(Club, pk=pk)
  membership = club.memberships.filter(status='approved')
  pending_requests = (
      club.memberships.filter(status='pending')
      if request.user == club.president
      else None
  )

  user_membership = None
  if request.user.is_authenticated:
    user_membership = club.memberships.filter(user=request.user).first()

  return render(
      request,
      'clubs/club_detail.html',
      {
          'club': club,
          'membership': membership,
          'pending_requests': pending_requests,
          'user_membership': user_membership,
      },
  )


# Club Creation
@login_required
def club_create(request):
  if request.method == 'POST':
    form = ClubForm(request.POST, request.FILES)
    if form.is_valid():
      club = form.save(commit=False)
      club.president = request.user
      club.save()

      Membership.objects.create(
          club=club, user=request.user, status='approved'
      )
      return redirect('club_detail', pk=club.pk)
  else:
    form = ClubForm()

  return render(
      request,
      'clubs/club_form.html',
      {'form': form, 'title': 'Create Club'},
  )


# Edit Club
@login_required
def club_edit(request, pk):
  club = get_object_or_404(Club, pk=pk)
  if request.user != club.president:
    messages.error(
        request, 'You do not have the authority to edit club information'
    )
    return redirect('club_detail', pk=club.pk)

  if request.method == 'POST':
    form = ClubForm(request.POST, request.FILES, instance=club)
    if form.is_valid():
      form.save()
      messages.success(request, 'Club information updated successfully!')
      return redirect('club_detail', pk=club.pk)
  else:
    form = ClubForm(instance=club)

  return render(
      request,
      'clubs/club_form.html',
      {'form': form, 'title': 'Edit Club', 'club': club},
  )


# Delete Club
@login_required
def club_delete(request, pk):
  club = get_object_or_404(Club, pk=pk)
  if request.user != club.president:
    messages.error(
        request, 'You do not have the authority to delete this club'
    )
    return redirect('club_detail', pk=club.pk)

  if request.method == 'POST':
    club.delete()
    messages.success(request, 'Club deleted successfully')
    return redirect('club_list')

  return render(request, 'clubs/club_confirm_delete.html', {'club': club})


# Join Request
@login_required
def join_request(request, pk):
  club = get_object_or_404(Club, pk=pk)
  membership, created = Membership.objects.get_or_create(
      club=club, user=request.user
  )
  if created:
    messages.success(request, 'Membership request submitted successfully!')
  else:
    messages.info(request, 'You have already requested or joined this club.')
  return redirect('club_detail', pk=club.pk)


# Manage Request
@login_required
def manage_request(request, membership_id, action):
  membership = get_object_or_404(Membership, id=membership_id)
  if request.user != membership.club.president:
    messages.error(request, 'Permission denied')
    return redirect('club_detail', pk=membership.club.pk)

  if action == 'approve':
    membership.status = 'approved'
    messages.success(
        request, f'User {membership.user} accepted to the club.'
    )
  elif action == 'reject':
    membership.status = 'rejected'
    messages.info(request, f'Request from {membership.user} rejected.')

  membership.save()
  return redirect('club_detail', pk=membership.club.pk)