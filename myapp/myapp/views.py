from django.shortcuts import render

def home(request):
    """Simple homepage placeholder."""
    return render(request, 'home.html', { 'active_nav_item': 'home', 'page_title': 'Home' })
