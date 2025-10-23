from . import views
from django.urls import path # (If using Django)

urlpatterns = [
    # 1. Default Dashboard route (shows Multi-year Trends)
    path('', views.dashboard_trends_view, name='dashboard_trends'),
    path('trends/', views.dashboard_trends_view, name='dashboard_trends_explicit'), # Same view, explicit path

    # 2. 2025 Global Landscape route
    path('landscape/', views.dashboard_landscape_view, name='dashboard_landscape'),
]