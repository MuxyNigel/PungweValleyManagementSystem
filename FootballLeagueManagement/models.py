from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import F

class Season(models.Model):
    year = models.IntegerField(primary_key=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.year} Season"

class Division(models.Model):
    name = models.CharField(max_length=100, unique=True)
    tier = models.PositiveIntegerField(help_text="1 is the top tier (e.g. League A)")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['tier', 'name']

class Team(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='team_logos/')
    home_ground = models.ForeignKey('Venue', on_delete=models.SET_NULL, null=True, blank=True, related_name='home_teams')
    coach = models.CharField(max_length=100)
    manager = models.CharField(max_length=100, null=True, blank=True)
    year_established = models.PositiveIntegerField(null=True, blank=True)
    history = models.TextField(null=True, blank=True)
    contact_details = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='Contact details must contain only numbers.',
            ),
            MinLengthValidator(10, message='Contact number must be at least 10 digits long.')
        ]
    )

    def __str__(self):
        return self.name
    
class Player(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='player_photos/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=50, null=True, blank=True)
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    position = models.CharField(max_length=50)
    goals = models.PositiveIntegerField(default=0)  # New field for goals scored
    assists = models.PositiveIntegerField(default=0)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Referee(models.Model):
    name = models.CharField(max_length=100)
    home_area = models.CharField(max_length=50)
    contact_details = models.CharField(
        max_length=10,
         null=True,
         blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='Contact details must be exactly 10 digits.',
                code='invalid_contact_details'
            ),
        ],
    )
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name

class Venue(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name

class Match(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Postponed', 'Postponed'),
    ]
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    home_team_score = models.PositiveIntegerField(null=True, blank=True)
    away_team_score = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Scheduled')  # e.g., Scheduled, Completed
    report = models.TextField(null=True, blank=True, help_text="Match report and summary.")

    def clean(self):
        if self.home_team_id == self.away_team_id:
            raise ValidationError("Home and away team cannot be the same.")
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.date}"

class MatchRef(models.Model):
    STATUS_CHOICES = [
        ('Center', 'Center'),
        ('Assistant1', 'Assistant1'),
        ('Assistant2', 'Assistant2'),
    ]
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    ref = models.ForeignKey(Referee, on_delete=models.CASCADE)
    ref_type = models.CharField(max_length=20, choices=STATUS_CHOICES)  # e.g., 'Center', 'Assistant1', 'Assistant2'

    def clean(self):
        # If match isn't saved yet (e.g., creating a Match with inlines in admin),
        # skip DB lookups - the inline formset will validate duplicates among submitted forms.
        if not getattr(self, 'match_id', None):
            super().clean()
            return
        # Prevent duplicate roles for the same match
        if MatchRef.objects.filter(match=self.match, ref_type=self.ref_type).exclude(pk=self.pk).exists():
            raise ValidationError(f"A {self.ref_type} referee has already been allocated to this match.")
        # Prevent same referee being added multiple times to the same match
        if MatchRef.objects.filter(match=self.match, ref=self.ref).exclude(pk=self.pk).exists():
            raise ValidationError("This official has already been allocated to this match.")
        # Prevent a referee from being assigned to a different match on the same date
        if MatchRef.objects.filter(ref=self.ref, match__date=self.match.date).exclude(match=self.match).exists():
            raise ValidationError(f"{self.ref.name} is already assigned to another match on {self.match.date}.")
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['match', 'ref_type'], name='unique_match_ref_type'),
            models.UniqueConstraint(fields=['match', 'ref'], name='unique_match_ref_assign'),
        ]

class Card(models.Model):
    STATUS_CHOICES = [
        ('Yellow', 'Yellow'),
        ('Red', 'Red'),
    ]
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    card_type = models.CharField(max_length=10, choices=STATUS_CHOICES)

class MatchIssue(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Resolved', 'Resolved'),
    ]
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    ref = models.ForeignKey(Referee, on_delete=models.CASCADE)
    issue_type = models.CharField(max_length=50)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')

class Fine(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    ]
    ENTITY_CHOICES = [
        ('Player', 'Player'),
        ('Team', 'Team'),
        ('Referee', 'Referee'),
    ]
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    entity_type = models.CharField(max_length=20, choices=ENTITY_CHOICES)  # 'Player', 'Team', 'Referee'
    entity_name = models.CharField(max_length=150, null=True, blank=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.entity_type}: {self.entity_name} - {self.amount}"

class Contract(models.Model):
    ENTITY_CHOICES = [
        ('Player', 'Player'),
        ('Referee', 'Referee'),
        ('Coach', 'Coach'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Expired', 'Expired'),
    ]
    entity_type = models.CharField(max_length=20, choices=ENTITY_CHOICES)  # 'Player', 'Referee', etc.
    entity_name = models.CharField(max_length=150, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    terms = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return f"{self.entity_type}: {self.entity_name} ({self.status})"

# You can extend the User model for roles
# models.py
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    role = models.CharField(max_length=20)

    # Override to avoid reverse accessor clash
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # change to a unique name
        blank=True,
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # change to a unique name
        blank=True,
        verbose_name='user permissions'
    )

class NewsArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)
    published_date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=100, default='League Admin')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_date']

class Sponsor(models.Model):
    SPONSOR_TYPES = [
        ('League', 'League Sponsor'),
        ('Team', 'Team Sponsor'),
    ]
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='sponsor_logos/')
    website_url = models.URLField(max_length=200, null=True, blank=True)
    sponsor_type = models.CharField(max_length=20, choices=SPONSOR_TYPES, default='League')

    def __str__(self):
        return f"{self.name} ({self.sponsor_type})"

class Rule(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Order in which this rule appears.")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']

class TransferHistory(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='transfer_history')
    from_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_out')
    to_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='transfers_in')
    transfer_date = models.DateField()
    transfer_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    details = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.player.name}: {self.from_team} -> {self.to_team} on {self.transfer_date}"

    class Meta:
        ordering = ['-transfer_date']

class PromotionRelegation(models.Model):
    STATUS_CHOICES = [
        ('Promoted', 'Promoted'),
        ('Relegated', 'Relegated'),
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='promotions_relegations')
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    from_division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='from_records')
    to_division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='to_records')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.team.name} - {self.status} to {self.to_division.name} ({self.season.year})"

class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    scorer = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals_scored')
    assist = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='goals_assisted')
    minute = models.PositiveIntegerField()

    is_own_goal = models.BooleanField(default=False)

    def __str__(self):
        return f"Goal by {self.scorer.name} at {self.minute}'"

    class Meta:
        ordering = ['minute']

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Goal)
def update_player_stats_on_save(sender, instance, **kwargs):
    if not instance.is_own_goal:
        scorer = instance.scorer
        scorer.goals = Goal.objects.filter(scorer=scorer, is_own_goal=False).count()
        scorer.save(update_fields=['goals'])
    
    if instance.assist:
        assist = instance.assist
        assist.assists = Goal.objects.filter(assist=assist).count()
        assist.save(update_fields=['assists'])

@receiver(post_delete, sender=Goal)
def update_player_stats_on_delete(sender, instance, **kwargs):
    if not instance.is_own_goal:
        scorer = instance.scorer
        scorer.goals = Goal.objects.filter(scorer=scorer, is_own_goal=False).count()
        scorer.save(update_fields=['goals'])
    
    if instance.assist:
        assist = instance.assist
        assist.assists = Goal.objects.filter(assist=assist).count()
        assist.save(update_fields=['assists'])