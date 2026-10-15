<<<<<<< HEAD
from django.conf import settings
from django.db import models
=======
>>>>>>> origin/main


class Club(models.Model):
  MAX_LENGTH_NAME = 50
  MAX_LENGTH_DESC = 1000

  CATEGORY_CHOICES = [
      ('sports', 'Sports'),
      ('arts', 'Arts'),
      ('academic', 'Academic'),
      ('science', 'Science'),
      ('social', 'Social Activities'),
  ]

  name = models.CharField(
      max_length=MAX_LENGTH_NAME,
      unique=True,
  )
  description = models.TextField(max_length=MAX_LENGTH_DESC)
  category = models.CharField(
      max_length=MAX_LENGTH_NAME,
      choices=CATEGORY_CHOICES,
      default='social',
  )
  president = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='managed_clubs',
  )
  logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
  created_at = models.DateTimeField(
      auto_now_add=True,
  )

  def __str__(self):
    return self.name


class Membership(models.Model):
  MAX_LENGTH_NAME = 50

  STATUS_CHOICES = [
      ('pending', 'Pending'),
      ('approved', 'Approved'),
      ('rejected', 'Rejected'),
  ]

  club = models.ForeignKey(
      Club, on_delete=models.CASCADE, related_name='memberships'
  )
  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='memberships',
  )
  status = models.CharField(
      max_length=MAX_LENGTH_NAME, choices=STATUS_CHOICES, default='pending'
  )
  joined_at = models.DateTimeField(
      auto_now_add=True,
  )

  class Meta:
    unique_together = ('club', 'user')

  def __str__(self):
    return f'{self.user.email} - {self.club.name} ({self.status})'