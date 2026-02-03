from django.contrib import admin
from .models import (
    Team, Player, Referee, Venue, Match,
    MatchRef, Card, MatchIssue, Fine, Contract, CustomUser, Season
)

# Customize admin site titles
admin.site.site_header = "Pungwe Valley Football League Management"
admin.site.site_title = "Pungwe Valley Admin Portal"
admin.site.index_title = "Dashboard"

# Inline admin for Card inside Match
class CardInline(admin.TabularInline):
    model = Card
    extra = 1

# Inline admin for MatchRef inside Match
class MatchRefInline(admin.TabularInline):
    model = MatchRef
    extra = 1

# Admin for Team
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'coach', 'contact_details')
    search_fields = ('name', 'coach')

# Admin for Player
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'position')
    list_filter = ('team', 'position')
    search_fields = ('name',)

# Admin for Referee
@admin.register(Referee)
class RefereeAdmin(admin.ModelAdmin):
    list_display = ('name', 'home_area', 'contact_details')
    search_fields = ('name', 'home_area')

# Admin for Venue
@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

# Admin for Match
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'away_team', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('home_team__name', 'away_team__name')
    inlines = [MatchRefInline, CardInline]

# Admin for MatchRef
@admin.register(MatchRef)
class MatchRefAdmin(admin.ModelAdmin):
    list_display = ('match', 'ref', 'ref_type')
    list_filter = ('ref_type',)
    search_fields = ('match__home_team__name', 'match__away_team__name', 'ref__name')

# Admin for Card
@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('player', 'match', 'card_type')
    list_filter = ('card_type', 'match')
    search_fields = ('player__name',)

# Admin for MatchIssue
@admin.register(MatchIssue)
class MatchIssueAdmin(admin.ModelAdmin):
    list_display = ('match', 'team', 'ref', 'issue_type', 'status')
    list_filter = ('issue_type', 'status', 'team')
    search_fields = ('match__home_team__name', 'match__away_team__name', 'ref__name')

# Admin for Fine
@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'entity_id', 'amount', 'reason')
    search_fields = ('reason',)

# Admin for Contract
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    # Note: No 'player', 'team', or 'salary' fields in your model
    # Adjusted to display 'entity_type', 'entity_id', 'start_date', 'end_date', 'status'
    list_display = ('entity_type', 'entity_id', 'start_date', 'end_date', 'status')
    list_filter = ('entity_type', 'status')
    search_fields = ('entity_type',)

# Admin for CustomUser
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser')

# Admin for Season
@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'description')
    search_fields = ('year', 'description')
    list_filter = ('year', 'start_date', 'end_date')
       