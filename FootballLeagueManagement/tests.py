from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time

from .models import Team, Match, Referee, MatchRef
from .admin import MatchRefInlineFormset


class MatchValidationTests(TestCase):
    def setUp(self):
        self.team1 = Team.objects.create(name='Team A', logo='logo.png', coach='Coach A')
        self.team2 = Team.objects.create(name='Team B', logo='logo2.png', coach='Coach B')
        self.ref1 = Referee.objects.create(name='Ref One', home_area='Area1')
        self.ref2 = Referee.objects.create(name='Ref Two', home_area='Area2')
        # create a Venue so Match can be created
        from .models import Venue
        self.venue = Venue.objects.create(name='Ground 1', location='Loc 1')

    def test_match_same_team_validation(self):
        # home and away cannot be the same
        m = Match(home_team=self.team1, away_team=self.team1, date=date.today(), time=time(12, 0), venue=None)
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_matchref_duplicate_role_model_validation(self):
        # Assign a Center ref then try to add another Center via model validation
        m = Match.objects.create(home_team=self.team1, away_team=self.team2, date=date.today(), time=time(12, 0), venue=None)
        MatchRef.objects.create(match=m, ref=self.ref1, ref_type='Center')
        mr = MatchRef(match=m, ref=self.ref2, ref_type='Center')
        with self.assertRaises(ValidationError):
            mr.full_clean()

    def test_matchref_duplicate_official_model_validation(self):
        # Assign a ref to the match then try to assign same ref again
        m = Match.objects.create(home_team=self.team1, away_team=self.team2, date=date.today(), time=time(12, 0), venue=None)
        MatchRef.objects.create(match=m, ref=self.ref1, ref_type='Center')
        mr = MatchRef(match=m, ref=self.ref1, ref_type='Assistant1')
        with self.assertRaises(ValidationError):
            mr.full_clean()

    def test_matchref_inline_formset_duplicate_detection(self):
        # Use inlineformset_factory to simulate admin inline submissions for an unsaved Match
        from django.forms.models import inlineformset_factory

        FormSet = inlineformset_factory(Match, MatchRef, formset=MatchRefInlineFormset, fields=('ref', 'ref_type'), extra=2)
        m = Match()  # unsaved
        fs = FormSet(instance=m)
        prefix = fs.prefix

        # Two forms with same ref_type
        post_data = {
            f'{prefix}-TOTAL_FORMS': '2',
            f'{prefix}-INITIAL_FORMS': '0',
            f'{prefix}-MIN_NUM_FORMS': '0',
            f'{prefix}-MAX_NUM_FORMS': '1000',
            f'{prefix}-0-ref': str(self.ref1.pk),
            f'{prefix}-0-ref_type': 'Center',
            f'{prefix}-1-ref': str(self.ref2.pk),
            f'{prefix}-1-ref_type': 'Center',
        }
        fs2 = FormSet(data=post_data, instance=m)
        self.assertFalse(fs2.is_valid())
        self.assertTrue(fs2.non_form_errors())

        # Two forms with same ref
        post_data = {
            f'{prefix}-TOTAL_FORMS': '2',
            f'{prefix}-INITIAL_FORMS': '0',
            f'{prefix}-MIN_NUM_FORMS': '0',
            f'{prefix}-MAX_NUM_FORMS': '1000',
            f'{prefix}-0-ref': str(self.ref1.pk),
            f'{prefix}-0-ref_type': 'Assistant1',
            f'{prefix}-1-ref': str(self.ref1.pk),
            f'{prefix}-1-ref_type': 'Assistant2',
        }
        fs3 = FormSet(data=post_data, instance=m)
        self.assertFalse(fs3.is_valid())
        self.assertTrue(fs3.non_form_errors())
