from django.db.utils import OperationalError, ProgrammingError
from .models import Team


def site_context(request):
    """Add teams to template context for global access.

    Resilient to missing tables to avoid crashing during initial setup.
    """
    try:
        teams = Team.objects.all()
    except (OperationalError, ProgrammingError):
        teams = Team.objects.none()

    return {
        'site_teams': teams,
    }