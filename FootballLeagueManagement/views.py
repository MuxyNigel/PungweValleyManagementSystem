from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, F, Sum, Case, When
from collections import defaultdict, Counter
from datetime import datetime

from .models import (
    Match,
    MatchRef,
    Card,
    MatchIssue,
    Team,
    Player,
    Season,
    Referee,
    Venue,
)


# -------------------------
# Home view
# -------------------------
def home(request):
    return render(request, 'football/home.html')


# -------------------------
# List all matches
# -------------------------
def match_list(request):
    # Show all matches by default, allow filtering by status (Completed, Scheduled, Cancelled, Postponed)
    matches = Match.objects.select_related(
        'home_team', 'away_team', 'venue'
    ).order_by('date', 'time')

    # Apply optional filters from GET params
    home_team = request.GET.get('home_team')
    away_team = request.GET.get('away_team')
    year = request.GET.get('year')
    date = request.GET.get('date')
    status = request.GET.get('status')

    if home_team:
        matches = matches.filter(home_team_id=home_team)
    if away_team:
        matches = matches.filter(away_team_id=away_team)
    if year:
        matches = matches.filter(date__year=year)
    if date:
        matches = matches.filter(date=date)
    if status:
        matches = matches.filter(status=status)

    teams = Team.objects.all()
    years = [d.year for d in Match.objects.dates('date', 'year')]
    statuses = [choice[0] for choice in Match.STATUS_CHOICES]

    return render(request, 'football/match_list.html', {
        'matches': matches,
        'teams': teams,
        'years': years,
        'statuses': statuses,
    })


# -------------------------
# Match detail view
# -------------------------
def match_detail(request, match_id):
    match = get_object_or_404(
        Match.objects.select_related(
            'home_team', 'away_team', 'venue'
        ),
        id=match_id
    )

    referees = MatchRef.objects.filter(match=match).select_related('ref')
    cards = Card.objects.filter(match=match).select_related('player')
    issues = MatchIssue.objects.filter(match=match)

    return render(request, 'football/match_detail.html', {
        'match': match,
        'referees': referees,
        'cards': cards,
        'issues': issues
    })


# -------------------------
# League standings view
# -------------------------
def league_standings(request):
    # Filters
    year = request.GET.get('year')
    scope = request.GET.get('scope', '')  # '', 'home', 'away' 

    # Seasons for filter dropdown
    seasons = Season.objects.order_by('-year')

    # Base matches queryset (filtered by season/year if provided)
    matches_qs = Match.objects.select_related('home_team', 'away_team')
    if year:
        matches_qs = matches_qs.filter(season__year=year)

    # Only consider matches that are Completed for table calculations
    matches_qs = matches_qs.filter(status='Completed')

    # If week provided, optionally filter matches to that week (assumes you mark a 'week' somewhere; here we filter by date range if needed)
    # For now we'll accept week as informational only; no automatic mapping to dates unless you provide week->date logic.

    # Teams
    teams = Team.objects.all()

    # Build standings according to scope
    standings = []
    total_teams = teams.count()

    for team in teams:
        matches = matches_qs.filter(Q(home_team=team) | Q(away_team=team))

        if scope == 'home':
            matches = matches.filter(home_team=team)
        elif scope == 'away':
            matches = matches.filter(away_team=team)

        played = matches.count()

        wins = matches.filter(
            (Q(home_team=team) & Q(home_team_score__gt=F('away_team_score'))) |
            (Q(away_team=team) & Q(away_team_score__gt=F('home_team_score')))
        ).count()

        draws = matches.filter(
            Q(home_team=team, home_team_score=F('away_team_score')) |
            Q(away_team=team, away_team_score=F('home_team_score'))
        ).count()

        losses = played - wins - draws

        goals_for = matches.aggregate(
            total=Sum(
                Case(
                    When(home_team=team, then=F('home_team_score')),
                    When(away_team=team, then=F('away_team_score')),
                )
            )
        )['total'] or 0

        goals_against = matches.aggregate(
            total=Sum(
                Case(
                    When(home_team=team, then=F('away_team_score')),
                    When(away_team=team, then=F('home_team_score')),
                )
            )
        )['total'] or 0

        goal_difference = goals_for - goals_against
        points = wins * 3 + draws

        standings.append({
            'team': team,
            'played': played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goal_difference': goal_difference,
            'points': points
        })

    # If no completed matches exist yet, show all teams alphabetically (league not started)
    any_played = any(entry['played'] > 0 for entry in standings)

    if not any_played:
        # League not started: alphabetical A→Z
        standings.sort(key=lambda x: x['team'].name.lower())
    else:
        # Keep all teams visible: played teams first (competitive order), then zero-played teams alphabetically
        played_entries = [entry for entry in standings if entry['played'] > 0]
        zero_entries = [entry for entry in standings if entry['played'] == 0]

        # Sort played entries by Points → Goal Difference → Goals Scored (descending)
        played_entries.sort(
            key=lambda x: (x['points'], x['goal_difference'], x['goals_for']),
            reverse=True
        )

        # Sort zero-played entries alphabetically A→Z
        zero_entries.sort(key=lambda x: x['team'].name.lower())

        # Concatenate lists so played teams appear first
        standings = played_entries + zero_entries

    # Recompute total teams after ordering
    total_teams = len(standings)

    # Add position & row color (positions reflect current ordering)
    for index, entry in enumerate(standings):
        position = index + 1
        entry['position'] = position

        if position == 1:
            entry['row_class'] = 'champion'
        elif 2 <= position <= 5:
            entry['row_class'] = 'top-five'
        elif position > total_teams - 3:
            entry['row_class'] = 'relegation'
        else:
            entry['row_class'] = ''

    # Determine automatic week based on majority 'played' (P) among teams with played > 0
    played_counts = Counter(entry['played'] for entry in standings if entry['played'] > 0)
    if played_counts:
        # choose the played value with highest frequency, tie break by larger played value
        computed_week = max(played_counts.items(), key=lambda x: (x[1], x[0]))[0]
    else:
        # default to week 1 when no matches played yet so header shows 'WEEK 1'
        computed_week = 1

    # Send data to template
    context = {
        'standings': standings,
        'seasons': seasons,
        'selected_year': year,
        'selected_scope': scope,
        'teams': teams,
        'computed_week': computed_week,
    }

    # Notice list and team search endpoints are module-level views (see below)
    return render(request, 'football/league_table.html', context)





# -------------------------
# Team search (JSON) - used by navbar autocomplete
# -------------------------
from django.views.decorators.http import require_GET

@require_GET
def team_search(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        qs = Team.objects.filter(name__icontains=q).order_by('name')[:10]
        results = [{'id': t.id, 'name': t.name} for t in qs]
    return JsonResponse(results, safe=False)


# -------------------------
# Team profile view
# -------------------------
def team_profile(request, team_id):
    team = get_object_or_404(Team, id=team_id)

    players = Player.objects.filter(team=team)

    matches_as_home = Match.objects.filter(home_team=team)
    matches_as_away = Match.objects.filter(away_team=team)

    recent_matches = (matches_as_home | matches_as_away).order_by('-date')[:5]

    return render(request, 'football/team_profile.html', {
        'team': team,
        'players': players,
        'recent_matches': recent_matches
    })


# -------------------------
# Referees list and filter view
# -------------------------

def referees(request):
    refs = Referee.objects.all().order_by('name')
    selected_ref = request.GET.get('ref')
    team = request.GET.get('team')
    date = request.GET.get('date')

    matches = None
    if selected_ref:
        matches = Match.objects.filter(matchref__ref_id=selected_ref).select_related('home_team', 'away_team', 'venue').distinct().order_by('-date')
        if team:
            matches = matches.filter(Q(home_team_id=team) | Q(away_team_id=team))
        if date:
            matches = matches.filter(date=date)

    teams = Team.objects.all()
    return render(request, 'football/referees.html', {
        'refs': refs,
        'matches': matches,
        'teams': teams,
        'selected_ref': selected_ref
    })


# -------------------------
# Referee detail view
# -------------------------

def referee_detail(request, ref_id):
    ref = get_object_or_404(Referee, id=ref_id)
    # matches they officiated (including role)
    matchrefs = MatchRef.objects.filter(ref=ref).select_related('match__home_team', 'match__away_team', 'match__venue', 'match').order_by('-match__date')

    matches = []
    center_matches = []
    for mr in matchrefs:
        match = mr.match
        officials = MatchRef.objects.filter(match=match).select_related('ref')
        matches.append({
            'match': match,
            'officials': officials,
            'ref_type': mr.ref_type
        })
        if mr.ref_type == 'Center':
            center_matches.append(match)

    # upcoming matches (not completed, date in future)
    from django.utils import timezone
    today = timezone.now().date()
    upcoming = Match.objects.filter(matchref__ref=ref, date__gte=today).select_related('home_team', 'away_team', 'venue').order_by('date').distinct()

    # Compute per-team stats (only for matches where this referee was Center)
    team_stats = {}
    if center_matches:
        for m in center_matches:
            # update played
            for t in (m.home_team, m.away_team):
                if t.id not in team_stats:
                    team_stats[t.id] = {'team': t, 'played': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'yellow_cards': 0, 'red_cards': 0}
                team_stats[t.id]['played'] += 1

            # results
            if m.home_team_score is not None and m.away_team_score is not None:
                if m.home_team_score > m.away_team_score:
                    team_stats[m.home_team.id]['wins'] += 1
                    team_stats[m.away_team.id]['losses'] += 1
                elif m.home_team_score < m.away_team_score:
                    team_stats[m.away_team.id]['wins'] += 1
                    team_stats[m.home_team.id]['losses'] += 1
                else:
                    team_stats[m.home_team.id]['draws'] += 1
                    team_stats[m.away_team.id]['draws'] += 1

            # cards
            cards = Card.objects.filter(match=m).select_related('player')
            for c in cards:
                t = c.player.team
                if t.id not in team_stats:
                    team_stats[t.id] = {'team': t, 'played': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'yellow_cards': 0, 'red_cards': 0}
                if c.card_type == 'Yellow':
                    team_stats[t.id]['yellow_cards'] += 1
                elif c.card_type == 'Red':
                    team_stats[t.id]['red_cards'] += 1

    # turn dict into list for template
    team_stats_list = [v for v in team_stats.values()]

    return render(request, 'football/referee_detail.html', {
        'referee': ref,
        'matches': matches,
        'upcoming': upcoming,
        'team_stats': team_stats_list
    })


# -------------------------
# Top scorers view
# -------------------------
def top_scorers(request):
    players = Player.objects.all().order_by('-goals')[:10]

    return render(request, 'football/top_scorers.html', {
        'players': players
    })

# -------------------------
#. discipline view
# -------------------------
def get_player_discipline(request):
    # Allow filtering by season (year) via GET; default to latest season
    season_year = request.GET.get('season')
    if season_year:
        season = Season.objects.filter(year=season_year).first()
    else:
        season = Season.objects.order_by('-year').first()

    if season:
        cards = Card.objects.select_related('player', 'match').filter(season=season).order_by('player', 'match__date')
    else:
        # fallback: all cards
        cards = Card.objects.select_related('player', 'match').order_by('player', 'match__date')

    # Prepare a dict to hold per-player card info
    player_cards = defaultdict(list)

    # Group cards by player
    for card in cards:
        player_cards[card.player.id].append(card)

    # For each player, analyze cards
    player_discipline_info = []

    # compute mid-season date if possible
    if season and season.start_date and season.end_date:
        mid_season_date = season.start_date + (season.end_date - season.start_date) / 2
    else:
        # approximate using first and last card dates
        dates = [c.match.date for c in cards]
        if dates:
            dates.sort()
            mid_index = len(dates) // 2
            mid_season_date = dates[mid_index]
        else:
            mid_season_date = None

    for player_id, card_list in player_cards.items():
        # Sort cards by match date
        card_list.sort(key=lambda c: c.match.date)

        yellow_streak = 0
        suspensions = []

        for index, card in enumerate(card_list):
            if card.card_type == 'Yellow':
                yellow_streak += 1
                # Check for 3 consecutive yellows
                if yellow_streak == 3:
                    # Player suspended for next match
                    suspensions.append({
                        'type': 'Yellow streak',
                        'match': card.match,
                        'reason': '3 consecutive yellows'
                    })
                    yellow_streak = 0  # reset streak after suspension
            elif card.card_type == 'Red':
                # Straight red, next 3 matches missed
                suspensions.append({
                    'type': 'Straight Red',
                    'match': card.match,
                    'reason': 'Red card'
                })
                yellow_streak = 0
            else:
                # For other card types if any
                pass

        # Check if total yellow cards before mid-season exceeds 5
        if mid_season_date:
            total_yellows_before_mid = sum(1 for c in card_list if c.card_type == 'Yellow' and c.match.date <= mid_season_date)
            if total_yellows_before_mid >= 5:
                suspensions.append({
                    'type': 'Yellow accumulation',
                    'reason': '5 yellow cards before mid-season'
                })

        # Add to result
        player = Player.objects.get(id=player_id)
        total_yellows = sum(1 for c in card_list if c.card_type == 'Yellow')
        total_reds = sum(1 for c in card_list if c.card_type == 'Red')
        player_discipline_info.append({
            'player': player,
            'total_yellows': total_yellows,
            'total_reds': total_reds,
            'suspensions': suspensions
        })

    # Pass this to template
    seasons = Season.objects.order_by('-year')
    return render(request, 'football/discipline.html', {'players': player_discipline_info, 'seasons': seasons, 'selected_season': season})

# -------------------------
# Venues list and detail view
# -------------------------

def venues(request):
    """Display all venues with optional filtering capabilities"""
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset
    venues_list = Venue.objects.all().order_by('name')
    
    # Apply search filter
    if search_query:
        venues_list = venues_list.filter(
            Q(name__icontains=search_query) | Q(location__icontains=search_query)
        )
    
    # Get venues with match statistics
    venues_data = []
    for venue in venues_list:
        matches_count = Match.objects.filter(venue=venue).count()
        completed_matches = Match.objects.filter(venue=venue, status='Completed').count()
        
        venues_data.append({
            'venue': venue,
            'matches_count': matches_count,
            'completed_matches': completed_matches,
        })
    
    return render(request, 'football/venues.html', {
        'venues_data': venues_data,
        'search_query': search_query,
        'total_venues': Venue.objects.count(),
    })


def venue_detail(request, venue_id):
    """Display detailed information about a specific venue"""
    venue = get_object_or_404(Venue, id=venue_id)
    
    # Get all matches at this venue
    matches = Match.objects.filter(venue=venue).select_related(
        'home_team', 'away_team'
    ).order_by('-date')
    
    # Categorize matches
    completed = matches.filter(status='Completed')
    scheduled = matches.filter(status='Scheduled')
    cancelled = matches.filter(status='Cancelled')
    
    # Stats
    total_matches = matches.count()
    total_goals = 0
    total_attendance = 0
    
    for match in completed:
        if match.home_team_score is not None and match.away_team_score is not None:
            total_goals += match.home_team_score + match.away_team_score
    
    return render(request, 'football/venue_detail.html', {
        'venue': venue,
        'matches': matches,
        'completed': completed,
        'scheduled': scheduled,
        'cancelled': cancelled,
        'stats': {
            'total_matches': total_matches,
            'total_goals': total_goals,
        }
    })