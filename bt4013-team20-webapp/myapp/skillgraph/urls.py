from django.urls import path
from . import views

app_name = 'skillgraph' 

urlpatterns = [
    path('', views.graph_view, name='view'),
]