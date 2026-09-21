from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),  # homepage
    path('matches/', views.match_list, name='match_list'),
    path('matches/<int:match_id>/', views.match_detail, name='match_detail'),
    path('standings/', views.league_standings, name='league_standings'),
    path('teams/<int:team_id>/', views.team_profile, name='team_profile'),
    path('teams/search/', views.team_search, name='team_search'),
    path('players/<int:player_id>/', views.player_profile, name='player_profile'),
    path('referees/', views.referees, name='referees'),
    path('referees/<int:ref_id>/', views.referee_detail, name='referee_detail'),
    path('top-scorers/', views.top_scorers, name='top_scorers'),
    # Add your new discipline URL
    path('discipline/', views.get_player_discipline, name='player_discipline'),
    path('venues/', views.venues, name='venues'),
    path('venues/<int:venue_id>/', views.venue_detail, name='venue_detail'),
    path('about/', views.about_us, name='about_us'),
    path('news/', views.news_list, name='news_list'),
    path('news/<int:article_id>/', views.news_detail, name='news_detail'),
    path('rules/', views.rules, name='rules'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
]