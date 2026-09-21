from django.contrib import admin
from .models import (
    Team, Player, Referee, Venue, Match,
    MatchRef, Card, MatchIssue, Fine, Contract, CustomUser, Season,
    NewsArticle, Sponsor, Rule, TransferHistory,
    Division, PromotionRelegation, Goal
)

# Customize admin site titles
admin.site.site_header = "PVPSL Management"
admin.site.site_title = "PVPSL Admin Portal"
admin.site.index_title = "League Management Dashboard"

# Inline admin for Card inside Match
class CardInline(admin.TabularInline):
    model = Card
    extra = 1

class GoalInline(admin.TabularInline):
    model = Goal
    extra = 1


class MatchRefInline(admin.TabularInline):
    model = MatchRef
    extra = 1
    #formset = MatchRefInlineFormset

# Admin for Team
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'coach', 'home_ground', 'year_established')
    search_fields = ('name', 'coach', 'manager')

# Admin for Player
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'position', 'jersey_number', 'national_id', 'date_of_birth')
    list_filter = ('team', 'position')
    search_fields = ('name', 'national_id')

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
    inlines = [MatchRefInline, GoalInline, CardInline]

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
    list_display = ('entity_type', 'entity_name', 'amount', 'reason')
    search_fields = ('reason','entity_name')

# Admin for Contract
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    # Note: No 'player', 'team', or 'salary' fields in your model
    # Adjusted to display 'entity_type', 'entity_name', 'start_date', 'end_date', 'status'
    list_display = ('entity_type', 'entity_name', 'start_date', 'end_date', 'status')
    list_filter = ('entity_type', 'status')
    search_fields = ('entity_type','entity_name')

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

# Admin for NewsArticle
@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_date', 'author')
    search_fields = ('title', 'content')
    list_filter = ('published_date', 'author')

# Admin for Sponsor
@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sponsor_type', 'website_url')
    search_fields = ('name',)
    list_filter = ('sponsor_type',)

# Admin for Rule
@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    search_fields = ('title', 'description')
    ordering = ('order',)
       
# Admin for TransferHistory
@admin.register(TransferHistory)
class TransferHistoryAdmin(admin.ModelAdmin):
    list_display = ('player', 'from_team', 'to_team', 'transfer_date', 'transfer_fee')
    list_filter = ('transfer_date', 'from_team', 'to_team')
    search_fields = ('player__name',)

# Admin for Division
@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier')
    ordering = ('tier',)

# Admin for PromotionRelegation
@admin.register(PromotionRelegation)
class PromotionRelegationAdmin(admin.ModelAdmin):
    list_display = ('team', 'season', 'status', 'from_division', 'to_division')
    list_filter = ('season', 'status', 'from_division', 'to_division')
    search_fields = ('team__name',)