from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def graph_view(request):
    """Renders the Skill Adjacency Graph page. Access limited to authenticated users."""
    context = {
        'page_title': 'Skill Adjacency Graph',
        'active_nav_item': 'skillgraph',
        'intro_message': 'This page will contain a D3.js or similar visualization showing skill relationships.'
    }
    return render(request, 'skillgraph/graph_view.html', context)

# # sample render function for context
# def render(request, template_name, context=None):
#     """
#     Conceptual function to simulate rendering a template with context.
#     Replace with your framework's actual render function.
#     """
#     print(f"Rendering template: {template_name}")
#     print(f"Context passed: {context}")
#     # In a real app, this would return an HttpResponse containing the rendered HTML
#     pass