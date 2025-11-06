from django.shortcuts import render

# Create your views here.
def dashboard_trends_view(request):
    """
    Renders the 'Multi-year Trends' page.
    This view is mapped to: / and /trends/
    """
    context = {
        # 1. Main Nav Highlight (Dashboard must be active)
        'active_nav_item': 'dashboard',

        # 2. Sub Nav Highlight (Multi-year Trends is the default active sub-item)
        'active_sub_nav': 'multi-year',

        # ... other data required for this page ...
    }
    # Renders the HTML template we created earlier (dashboard/templates/dashboard/dashboard_view.html)
    return render(request, 'dashboard/dashboard_view.html', context)

def dashboard_landscape_view(request):
    """
    Renders the '2025 Global Landscape' page.
    This view is mapped to: /landscape/
    """
    context = {
        # 1. Main Nav Highlight (Dashboard must be active)
        'active_nav_item': 'dashboard',

        # 2. Sub Nav Highlight (2025 Global Landscape must be active)
        'active_sub_nav': 'landscape',

        # ... other data required for this page ...
    }
    return render(request, 'dashboard/dashboard_view.html', context)