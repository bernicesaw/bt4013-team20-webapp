"""
Django Views for Career Chatbot
This file contains:
- The main chatbot UI view
- API endpoint for handling chatbot queries (async + sync versions)
- Health check endpoint for debugging system dependencies
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
import json
import time
import logging

# Import the agent executor that handles RAG queries
from .agents import career_rag_agent_executor

logger = logging.getLogger(__name__)


@never_cache
def chatbot_view(request):
    """
    Render the main chat interface template.
    never_cache → ensures the page always loads fresh (important for interactive apps).
    """
    return render(request, 'chatbot/chat.html', {
        'page_title': 'Career Chatbot',
        'user': request.user,  # Pass user info to template
        'active_nav_item': 'askai',   # For styling active navbar/menu
    })


@require_http_methods(["POST"])
async def query_chatbot_api(request):
    """
    ASYNC API endpoint:
    - Receives text from frontend
    - Sends it to the AI agent for processing
    - Returns structured JSON response
    
    async def allows Django to await the agent for improved performance
    when using async-capable LLM libraries.
    """
    start_time = time.time()  # Track response time for monitoring
    
    try:
        # Delay importing set_user_id until needed (avoids circular imports)
        from .agents import set_user_id
        
        # Parse incoming JSON or form-data depending on request type
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Fallback for form submissions
            data = {
                'text': request.POST.get('text', ''),
                'session_id': request.POST.get('session_id', 'default')
            }
        
        text = data.get('text', '').strip()
        session_id = data.get('session_id', 'default')

        logger.info(f"Received data: {data}")
        logger.info(f"Received query: {text}")
        
        # Validate that input text exists
        if not text:
            return JsonResponse({
                'success': False,
                'error': 'Text parameter is required'
            }, status=400)
        
        # Attach user ID to agent context for personalized recommendations
        if request.user.is_authenticated:
            set_user_id(request.user.id)
            logger.info(f"(ID: {request.user.id})")
        else:
            set_user_id(None)
            logger.info("Anonymous user")
        
        logger.info(f"Processing query: {text[:50]}...")
        
        # Call the RAG agent asynchronously
        result = await career_rag_agent_executor.ainvoke({"input": text})
        
        # Calculate response time
        response_time = time.time() - start_time
        
        logger.info(f"Query processed in {response_time:.2f}s")
        
        # Convert intermediate steps to strings for JSON serialization
        intermediate_steps = []
        if "intermediate_steps" in result:
            intermediate_steps = [
                str(step) for step in result["intermediate_steps"]
            ]
        
        # Send output back to frontend
        return JsonResponse({
            'success': True,
            'input': text,
            'output': result.get('output', 'No response generated'),
            'intermediate_steps': intermediate_steps,
            'response_time': round(response_time, 2)
        })
        
    except Exception as e:
        # Log traceback for debugging
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint:
    - Verifies that the Django server is running
    - Confirms Neo4j + Supabase vector store connectivity
    - Useful for monitoring uptime and debugging failures
    
    GET /askai/api/health/
    """
    try:
        # Import chains to verify initialization
        from .chains import career_cypher_chain, qa_chain
        
        # Basic system summary
        health_status = {
            'status': 'healthy',
            'django': 'running',
            'career_chain': 'initialized',
            'course_chain': 'initialized',
            'agent': 'initialized'
        }
        
        # Test Neo4j connectivity
        try:
            from .chains import graph
            graph.query("RETURN 1 as test")  # Simple test query
            health_status['neo4j'] = 'connected'
        except Exception as e:
            health_status['neo4j'] = f'error: {str(e)}'
        
        # Test Supabase / PGVector connectivity
        try:
            from .chains import supabase_vector_store
            # Simple test query
            supabase_vector_store.similarity_search("test", k=1)
            health_status['supabase'] = 'connected'
        except Exception as e:
            health_status['supabase'] = f'error: {str(e)}'
        
        return JsonResponse(health_status)
        
    except Exception as e:
        # If anything fails, return unhealthy
        return JsonResponse({
            'status': 'unhealthy',
            'django': 'running',
            'error': str(e)
        }, status=503)


@require_http_methods(["POST"])
def query_chatbot_sync(request):
    """
    Synchronous fallback endpoint:
    Use this if async views are not supported or malfunctioning in the Django setup.
    
    Identical logic to async version but without 'await'.
    """
    start_time = time.time()
    
    try:
        # Parse incoming request (JSON or form-data)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {
                'text': request.POST.get('text', ''),
                'session_id': request.POST.get('session_id', 'default')
            }
        
        text = data.get('text', '').strip()
        session_id = data.get('session_id', 'default')
        
        # Validate required input
        if not text:
            return JsonResponse({
                'success': False,
                'error': 'Text parameter is required'
            }, status=400)
        
        logger.info(f"Processing query (sync): {text[:50]}...")
        
        # Call the RAG agent synchronously
        result = career_rag_agent_executor.invoke({"input": text})
        
        # Compute execution time
        response_time = time.time() - start_time
        logger.info(f"Query processed in {response_time:.2f}s")
        
        # Make intermediate steps serialization-safe
        intermediate_steps = []
        if "intermediate_steps" in result:
            intermediate_steps = [
                str(step) for step in result["intermediate_steps"]
            ]
        
        return JsonResponse({
            'success': True,
            'input': text,
            'output': result.get('output', 'No response generated'),
            'intermediate_steps': intermediate_steps,
            'response_time': round(response_time, 2)
        })
        
    except Exception as e:
        # Log and return error cleanly
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)