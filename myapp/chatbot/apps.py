"""
Django App Configuration for Chatbot
This file defines configuration metadata for the Django app.
Django automatically loads this when the app is included in INSTALLED_APPS.
"""
from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    # Use BigAutoField as the default primary key type for all models in this app
    default_auto_field = 'django.db.models.BigAutoField'

    # Name of the Django app (must match the folder name)
    name = 'chatbot'

    # Human-readable name shown in Django Admin
    verbose_name = 'Career Chatbot'