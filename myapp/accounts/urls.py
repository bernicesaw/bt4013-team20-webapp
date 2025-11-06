"""
URL routing configuration for the accounts app.

Defines all URL patterns for authentication and profile management:
- Signup and signup success
- Login and logout
- Profile viewing and editing
- Settings management
"""
from django.urls import path
from .views import (
    signup_view,
    SimpleLoginView,
    logout_view,
    signup_success_view,
    profile_view,
    settings_view
)

app_name = 'accounts'

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('signup/success/', signup_success_view, name='signup_success'),
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),
    path('login/', SimpleLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
