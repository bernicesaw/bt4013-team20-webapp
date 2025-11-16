"""
URL Configuration for Chatbot App
"""
from django.urls import path
from . import views

# Namespace for reversing URLs within this app
app_name = 'chatbot'

urlpatterns = [
    # Main chat interface
    path('', views.chatbot_view, name='chat'),
    
    # Endpoint for handling chatbot queries (AJAX/REST requests from frontend)
    path('api/query/', views.query_chatbot_api, name='query'),  
    
    # Simple health check route for monitoring service availability
    path('api/health/', views.health_check, name='health'),
]