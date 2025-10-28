from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def chat_view(request):
	"""Placeholder AskAI / Chat view - requires login"""
	return render(request, 'chatbot/chat.html', { 'active_nav_item': 'chatbot', 'page_title': 'AskAI' })
