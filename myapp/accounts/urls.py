from django.urls import path
from .views import signup_view, SimpleLoginView, logout_view
from .views import signup_success_view

app_name = 'accounts'

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('signup/success/', signup_success_view, name='signup_success'),
    path('login/', SimpleLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]