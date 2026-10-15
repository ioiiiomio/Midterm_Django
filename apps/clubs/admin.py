from django.contrib import admin
from .models import Club, Membership


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
  list_display = ('name', 'category', 'president', 'created_at')
  list_filter = ('category', 'created_at')
  search_fields = ('name', 'description', 'president__email')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
  list_display = ('club', 'user', 'status', 'joined_at')
  list_filter = ('status', 'joined_at')
  search_fields = ('club__name', 'user__email')