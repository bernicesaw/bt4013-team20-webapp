from django.db import models
from django.contrib.auth.models import User

CURRENCY_CHOICES = [
    ('USD', 'USD'),
    ('SGD', 'SGD'),
    ('EUR', 'EUR'),
    ('GBP', 'GBP'),
]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    skills = models.JSONField(default=list)
    median_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')

    def __str__(self):
        return f"{self.user.email} profile"


class WorkExperience(models.Model):
    profile = models.ForeignKey(Profile, related_name='work_experiences', on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    skills = models.JSONField(default=list)
    median_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator

CURRENCY_CHOICES = [
    ('USD', 'USD'),
    ('SGD', 'SGD'),
    ('EUR', 'EUR'),
    ('GBP', 'GBP'),
    # add more as needed
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    skills = models.JSONField(default=list)  # list of skill strings, max 5 enforced in form
    median_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')

    def __str__(self):
        return f"{self.user.email} profile"

class WorkExperience(models.Model):
    profile = models.ForeignKey(Profile, related_name='work_experiences', on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    skills = models.JSONField(default=list)
    median_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']