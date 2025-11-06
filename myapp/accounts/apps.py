"""
Django app configuration for the accounts application.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration class for the accounts Django app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
