from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),  # homepage
    path('matches/', views.match_list, name='match_list'),
    path('matches/<int:match_id>/', views.match_detail, name='match_detail'),
    path('standings/', views.league_standings, name='league_standings'),
    path('teams/<int:team_id>/', views.team_profile, name='team_profile'),
    path('teams/search/', views.team_search, name='team_search'),
    path('referees/', views.referees, name='referees'),
    path('referees/<int:ref_id>/', views.referee_detail, name='referee_detail'),
    path('top-scorers/', views.top_scorers, name='top_scorers'),
    # Add your new discipline URL
    path('discipline/', views.get_player_discipline, name='player_discipline'),

]