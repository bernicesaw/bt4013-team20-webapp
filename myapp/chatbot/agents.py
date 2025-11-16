"""
Career RAG Agent for Django
Uses simple regex-based job title normalization with overlap handling
This module orchestrates the Career Graph, Vector Search, and Personalized Recommendation tools.
"""
import os
import re
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, Tool, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables (model names, API keys, etc.)
load_dotenv()
CAREER_AGENT_MODEL = os.getenv("CAREER_AGENT_MODEL")

# Import pre-defined chains (Cypher generator + course retriever)
from .chains import career_cypher_chain, qa_chain

# Helper functions for fetching user profile + formatting recommendations
from .recommendation_helper import (
    fetch_user_profile,
    format_recommendation_output
)

# Import vector store (used inside recommendation formatter)
from .chains import supabase_vector_store


# --- Job title synonyms dictionary ---
# Used to normalize user queries such as "backend dev" → "Developer, back-end"
SYNONYMS = {
    # Backend
    "backend dev": "Developer, back-end",
    "backend developer": "Developer, back-end",
    "back-end dev": "Developer, back-end",
    "back-end developer": "Developer, back-end",
    "backend engineer": "Developer, back-end",
    "be developer": "Developer, back-end",
    
    # Frontend
    "frontend dev": "Developer, front-end",
    "frontend developer": "Developer, front-end",
    "front-end dev": "Developer, front-end",
    "front-end developer": "Developer, front-end",
    "frontend engineer": "Developer, front-end",
    "fe developer": "Developer, front-end",
    
    # Full-stack
    "fullstack": "Developer, full-stack",
    "full stack": "Developer, full-stack",
    "fullstack developer": "Developer, full-stack",
    "full-stack dev": "Developer, full-stack",
    "full stack developer": "Developer, full-stack",
    "fs developer": "Developer, full-stack",
    
    # Data roles
    "data analyst": "Data or business analyst",
    "business analyst": "Data or business analyst",
    "analyst": "Data or business analyst",
    "ba": "Data or business analyst",
    "data scientist": "Data scientist",
    "ds": "Data scientist",
    "scientist": "Data scientist",
    "data engineer": "Data engineer",
    "de": "Data engineer",
    
    # AI/ML roles
    "ml engineer": "AI/ML engineer",
    "machine learning engineer": "AI/ML engineer",
    "ai engineer": "AI/ML engineer",
    "artificial intelligence engineer": "AI/ML engineer",
    "ai developer": "Developer, AI apps or physical AI",
    "ai app developer": "Developer, AI apps or physical AI",
    "physical ai developer": "Developer, AI apps or physical AI",
    "applied scientist": "Applied scientist",
    
    # Cloud/Infrastructure
    "cloud engineer": "Cloud infrastructure engineer",
    "cloud infrastructure": "Cloud infrastructure engineer",
    "infrastructure engineer": "Cloud infrastructure engineer",
    "sysadmin": "System administrator",
    "sys admin": "System administrator",
    "system admin": "System administrator",
    "devops": "DevOps engineer or professional",
    "devops engineer": "DevOps engineer or professional",
    "devops professional": "DevOps engineer or professional",
    
    # Database
    "database admin": "Database administrator or engineer",
    "dba": "Database administrator or engineer",
    "db admin": "Database administrator or engineer",
    "database administrator": "Database administrator or engineer",
    "database engineer": "Database administrator or engineer",
    
    # QA/Testing
    "qa": "Developer, QA or test",
    "qa engineer": "Developer, QA or test",
    "tester": "Developer, QA or test",
    "test engineer": "Developer, QA or test",
    "quality assurance": "Developer, QA or test",
    "qa developer": "Developer, QA or test",
    
    # Management
    "project manager": "Project manager",
    "pm": "Product manager",
    "product manager": "Product manager",
    "engineering manager": "Engineering manager",
    "eng manager": "Engineering manager",
    "em": "Engineering manager",
    
    # Security
    "security": "Cybersecurity or InfoSec professional",
    "cybersecurity": "Cybersecurity or InfoSec professional",
    "infosec": "Cybersecurity or InfoSec professional",
    "security engineer": "Cybersecurity or InfoSec professional",
    "security professional": "Cybersecurity or InfoSec professional",
    
    # Support
    "support engineer": "Support engineer or analyst",
    "support analyst": "Support engineer or analyst",
    "customer support": "Support engineer or analyst",
    
    # Design
    "ux": "UX, Research Ops or UI design professional",
    "ui": "UX, Research Ops or UI design professional",
    "ux designer": "UX, Research Ops or UI design professional",
    "ui designer": "UX, Research Ops or UI design professional",
    "designer": "UX, Research Ops or UI design professional",
    "ux researcher": "UX, Research Ops or UI design professional",
    
    # Executive/Leadership
    "cto": "Senior executive (C-suite, VP, etc.)",
    "ceo": "Senior executive (C-suite, VP, etc.)",
    "vp": "Senior executive (C-suite, VP, etc.)",
    "executive": "Senior executive (C-suite, VP, etc.)",
    "c-suite": "Senior executive (C-suite, VP, etc.)",
    "founder": "Founder, technology or otherwise",
    "co-founder": "Founder, technology or otherwise",
    
    # Specialized developers
    "researcher": "Academic researcher",
    "academic": "Academic researcher",
    "academic researcher": "Academic researcher",
    "mobile dev": "Developer, mobile",
    "mobile developer": "Developer, mobile",
    "mobile engineer": "Developer, mobile",
    "ios developer": "Developer, mobile",
    "android developer": "Developer, mobile",
    "game dev": "Developer, game or graphics",
    "game developer": "Developer, game or graphics",
    "graphics developer": "Developer, game or graphics",
    "desktop dev": "Developer, desktop or enterprise applications",
    "desktop developer": "Developer, desktop or enterprise applications",
    "enterprise developer": "Developer, desktop or enterprise applications",
    "embedded developer": "Developer, embedded applications or devices",
    "embedded engineer": "Developer, embedded applications or devices",
    "iot developer": "Developer, embedded applications or devices",
    
    # Architecture
    "architect": "Architect, software or solutions",
    "software architect": "Architect, software or solutions",
    "solutions architect": "Architect, software or solutions",
    "solution architect": "Architect, software or solutions",
    
    # Finance
    "financial analyst": "Financial analyst or engineer",
    "financial engineer": "Financial analyst or engineer",
    "quant": "Financial analyst or engineer",
}

# --- User context for personalized recommendations ---
_current_user_id = None # Stores the logged-in user ID globally for this module

def set_user_id(user_id: str):
    """Store current user ID so the personalized tool knows who is calling."""
    global _current_user_id
    _current_user_id = user_id
    print(f"👤 User ID set: {user_id}")

def get_user_id() -> str:
    """Return the active user ID (None if user not logged in)."""
    return _current_user_id

def personalized_recommendation_wrapper(query: str) -> str:
    """
    Main handler for personalized recommendations.
    Pulls the user profile → queries Neo4j directly → formats results with courses.
    """
    try:
        user_id = get_user_id()
        
        # Ensure user is logged in before accessing profile
        if not user_id:
            return "I need you to be logged in to generate personalized recommendations."
        
        # Fetch the user's saved profile (job title + skills)
        profile = fetch_user_profile(user_id)
        
        if not profile:
            return "I couldn't find your profile. Please make sure you've filled out your job title and skills in your profile."
        
        user_job = profile.get('job_title')
        user_skills = profile.get('skills', [])
        
        if not user_job:
            return "Please add your current job title to your profile first."
        
        print(f"👤 Generating recommendations for: {user_job}")
        print(f"📚 User skills: {user_skills}")
    
        
        # Query Neo4j graph directly instead of multi-step LangChain chain
        from .chains import graph
        
        # pre-defined function that aligns with skill graph recommendation method
        cypher_query = f"""
        MATCH (current:Job {{name: '{user_job}'}})-[r:RELATED_TO]->(related:Job)
        RETURN related.name AS job_name,
               related.top_language AS language,
               related.top_database AS database, 
               related.top_platform AS platform,
               related.top_webframe AS framework,
               related.median_comp AS salary,
               related.median_workexp AS experience,
               r.weight AS similarity
        ORDER BY r.weight ASC
        LIMIT 3
        """
        
        print(f"🔍 Executing Cypher query...")
        neo4j_results = graph.query(cypher_query)
        
        # Handle case where user job isn't in the graph
        if not neo4j_results:
            return f"I couldn't find any career recommendations for {user_job}. This might be because the job title isn't in our database."
        
        print(f"✅ Found {len(neo4j_results)} recommendations")
        
        # Format the output with courses using our own custom function in the recommendation_helper file
        formatted_output = format_recommendation_output(
            user_job=user_job,
            recommendations=neo4j_results,
            user_skills=user_skills,
            vector_store=supabase_vector_store # Pass vector DB for course enrichment
        )
        
        print(f"📝 Formatted output length: {len(formatted_output)} characters")
        
        return formatted_output # Final personalized recommendation answer to user
        
    except Exception as e:
        # Catch errors so agent does not crash
        print(f"❌ Error in personalized_recommendation_wrapper: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"I encountered an error generating your recommendations: {str(e)}"

# --- Agent prompt ---
career_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a career advisor assistant with access to three tools:

1. **PersonalizedCareerRecommendation** - for generating career recommendations based on user's profile
2. **CareerGraph** - for general job data, skills, salaries, and career information
3. **CourseRecommendations** - for finding courses and learning materials

TOOL SELECTION RULES:

Use **PersonalizedCareerRecommendation** when user asks:
- "Generate my career recommendation"
- "What career paths for me"
- "Recommend careers for me"
- "Career suggestions based on my profile"

Use **CareerGraph** for general queries:
- "Which jobs use Python?"
- "What skills does a data scientist need?"
- "Jobs similar to backend developer"

Use **CourseRecommendations** for learning materials:
- "Show me courses for Python"
- "Recommend learning materials for machine learning"

CRITICAL: Always pass the COMPLETE user query to the tool.

"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


import re

def normalize_job_title_in_query(query: str) -> str:
    """
    Normalize user-written job titles (slang, abbreviations, fuzzy descriptions)
    into valid Neo4j job titles.

    Example:
        "backend dev" → "Developer, back-end"
        "fs dev" → "Developer, full-stack"

    This ensures the Cypher generator always receives valid job titles.
    """

    # Create a set of all normalized values to avoid re-normalizing
    normalized_values = set(SYNONYMS.values())
    
    # If the whole query is exactly a normalized title, return as-is
    if query.strip() in normalized_values:
        return query.strip()
    
    # Sort keys longest→shortest to avoid partial matches breaking phrases
    sorted_synonyms = sorted(SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Track replacements to avoid overlaps
    replacements = []
    
    for title, normalized_title in sorted_synonyms:
        # Skip if we're trying to normalize to the same thing
        if title == normalized_title:
            continue
            
        # Escape special regex characters
        escaped_title = re.escape(title)
        
        # Word-boundary logic that works even with dashes/slashes/commas
        pattern = r'(?<![a-zA-Z0-9])' + escaped_title + r'(?![a-zA-Z0-9])'
        
        # Find all occurrences case-insensitively
        for match in re.finditer(pattern, query, flags=re.IGNORECASE):
            start, end = match.start(), match.end()
            
            # Avoid replacing inside already-replaced segments
            overlap = False
            for rep_start, rep_end, _ in replacements:
                if not (end <= rep_start or start >= rep_end):
                    overlap = True
                    break
            
            if not overlap:
                # Avoid replacing inside an already-normalized job title
                context_start = max(0, start - 50)
                context_end = min(len(query), end + 50)
                context = query[context_start:context_end]
                
                # Skip if this match is within a normalized value
                is_within_normalized = False
                for norm_value in normalized_values:
                    if norm_value in context and title in norm_value:
                        is_within_normalized = True
                        break
                
                if not is_within_normalized:
                    replacements.append((start, end, normalized_title))
    
    # Apply replacements from back-to-front so indices don't shift
    replacements.sort(key=lambda x: x[0], reverse=True)
    
    # Apply replacements
    result = query
    for start, end, normalized_title in replacements:
        result = result[:start] + normalized_title + result[end:]
    
    return result



def graph_chain_wrapper(query: str) -> str:
    """
    Wrapper for career graph queries:
    1. Normalize job titles in user query
    2. Pass normalized query to Cypher chain
    """
    try:
        # Normalize any job titles in the query
        normalized_query = normalize_job_title_in_query(query)
        
        # Pass the full normalized query to Cypher generation
        result = career_cypher_chain.invoke({"query": normalized_query})
        return result.get("result", str(result))
    
    except Exception as e:
        print(f"❌ Error in graph_chain_wrapper: {str(e)}")
        return f"I encountered an error querying the career database: {str(e)}"


def course_chain_wrapper(query: str) -> str:
    """
    Wrapper for course recommendation:
    1. Send raw user query to vector retriever chain
    2. Format response with REAL metadata URLs
    """
    try:
        print(f"Received query: {query}")
        
        result = qa_chain.invoke({"query": query})
        
        # If the chain returned retrieved documents, format manually
        if isinstance(result, dict) and "source_documents" in result:
            docs = result["source_documents"]

            if not docs:
                return "I couldn't find any relevant courses. Try different keywords."
            
            # Build numbered list with clickable URLs
            response = "Here are some recommended courses:\n\n"
            for i, doc in enumerate(docs, 1):
                title = doc.metadata.get('title', 'Unknown Course')
                url = doc.metadata.get('course_url', '#')
                response += f"{i}. [{title}]({url})\n"
            
            return response
        
        # Otherwise fallback to chain output
        return result.get("result", str(result))
    
    except Exception as e:
        print(f"❌ Error in course_chain_wrapper: {str(e)}")
        return f"I encountered an error searching for courses: {str(e)}"


# --- Define all agent tools ---
tools = [
    Tool(
        name="CourseRecommendations",
        func=course_chain_wrapper,
        description=(
            "Use for questions about courses, tutorials, learning materials, or certifications. "
            "IMPORTANT: Always pass the COMPLETE user query, not just keywords."
            "DO NOT use for non-tech topics like cooking, sports, art, music. "
            "If tool returns 'I don't have courses', DO NOT retry - accept the answer. "
        ),
    ),
    Tool(
        name="PersonalizedCareerRecommendation",
        func=personalized_recommendation_wrapper,
        description=(
            "Use ONLY when user asks for PERSONALIZED career recommendations like: "
            "'Generate my career recommendation', 'What career paths for me', 'Recommend careers for me'. "
            "This tool uses the user's profile (job title and skills) from the database. "
            "Pass the complete query."
        ),
        return_direct = True, # Skip agent summary and return tool output directly
    ),
    Tool(
        name="CareerGraph",
        func=graph_chain_wrapper,
        description=(
            "Use for general questions about jobs, careers, skills, technologies, salaries, or experience. "
            "IMPORTANT: Always pass the COMPLETE user query, not just keywords. "
            "Examples: 'What skills does X need?', 'Which jobs use Python?', 'Jobs similar to data scientist'"
        ),
    ),
]

# --- Initialize the LLM used by the agent ---
chat_model = ChatOpenAI(
    model=CAREER_AGENT_MODEL, # Model name loaded from .env
    temperature=0, # Deterministic actions (important for tools)
)


# --- Agent prompt: instructs how the agent chooses tools ---
career_rag_agent = create_openai_functions_agent(
    llm=chat_model,
    prompt=career_agent_prompt,
    tools=tools,
)


# --- Wrap agent in executor to enable execution + intermediate_steps ---
career_rag_agent_executor = AgentExecutor(
    agent=career_rag_agent,
    tools=tools,
    return_intermediate_steps=True, # Useful for debugging
    verbose=True, # Logs agent decisions in console
)


print("✅ Career RAG Agent initialized successfully")