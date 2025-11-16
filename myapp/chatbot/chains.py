"""
LangChain Chains for Career Chatbot
Contains both Career Graph and Course Recommendation chains.
This module initializes all LLM pipelines used by the chatbot.
"""
import os
from dotenv import load_dotenv
from langchain.chains import GraphCypherQAChain, RetrievalQA
from langchain_community.graphs import Neo4jGraph
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_openai import ChatOpenAI
from langchain_postgres.vectorstores import PGVector
from langchain_core.prompts import PromptTemplate
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)

# Load environment variables
load_dotenv()

# Load LLM + database configs from environment
CAREER_QA_MODEL = os.getenv("CAREER_AGENT_MODEL")
CAREER_CYPHER_MODEL = os.getenv("CAREER_AGENT_MODEL")
SUPABASE_CONNECTION_STRING = os.getenv("SUPABASE_POOLER_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ============================================
# CAREER GRAPH CHAIN (Neo4j)
# ============================================

# Create a Neo4j driver instance for querying the Career Graph
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
)

# Load the schema from Neo4j so the LLM can use node labels + property names
graph.refresh_schema()


# Prompt used for Cypher query generation from natural language
cypher_generation_prompt = PromptTemplate.from_template("""
Task: Generate a Cypher query for a Neo4j Career Graph database.

Schema:
{schema}

Node: :Job
Properties: name, median_comp, median_workexp, top_language, top_database, top_platform, top_webframe
Relationship: :RELATED_TO (has weight property - lower weight = more similar)

CRITICAL DATA FORMAT:
- Job names are EXACT strings (e.g., 'Data scientist', 'Developer, back-end')
- Technology fields (top_language, top_database, top_platform, top_webframe) contain COMMA-SEPARATED values
- Example: top_language = "Python, JavaScript, TypeScript, SQL"
- ALWAYS use CONTAINS for technology searches, NEVER use = for exact match
                                                        
EXAMPLE JOB NAMES (these are single, exact job names):
- 'Data or business analyst' (ONE job, not two)
- 'Developer, back-end' (ONE job with comma)
- 'Developer, front-end' (ONE job with comma)
- 'UX, Research Ops or UI design professional' (ONE job with both comma and or)
- 'AI/ML engineer' (ONE job with slash)

MATCHING RULES:
- For job names: Use exact match with = (e.g., WHERE j.name = 'Data scientist')
- For technologies: Use CONTAINS (e.g., WHERE j.top_language CONTAINS 'Python')
- Technology names are case-sensitive: 'Python' not 'python'

QUERY PATTERNS:

## Pattern 1: Job Properties (Skills, Salary, Experience)
Use when query asks about a SPECIFIC job's properties

Example: "What is the median salary for a Data scientist?"
MATCH (j:Job {{name: 'Data scientist'}})
RETURN j.median_comp AS median_salary

Example: "What is the work experience for Developer, back-end?"
MATCH (j:Job {{name: 'Developer, back-end'}})
RETURN j.median_workexp AS work_experience

Example: "What technologies does a Developer, full-stack use?"
MATCH (j:Job {{name: 'Developer, full-stack'}})
RETURN j.name AS job_title,
       j.top_language AS language, 
       j.top_database AS database, 
       j.top_platform AS platform, 
       j.top_webframe AS framework

Example: "What skills does a Data scientist need?"
MATCH (j:Job {{name: 'Data scientist'}})
RETURN j.top_language AS language, 
       j.top_database AS database, 
       j.top_platform AS platform, 
       j.top_webframe AS framework

## Pattern 2: Related/Similar Jobs
Use when query asks about jobs similar or related to a SPECIFIC job

Example: "What jobs are similar to Data scientist?"
MATCH (j:Job {{name: 'Data scientist'}})-[r:RELATED_TO]->(related:Job)
RETURN related.name AS job_name, r.weight AS similarity
ORDER BY r.weight ASC
LIMIT 10

Example: "Career transitions from Developer, back-end"
MATCH (j:Job {{name: 'Developer, back-end'}})-[r:RELATED_TO]->(related:Job)
RETURN related.name AS job_name, r.weight AS similarity
ORDER BY r.weight ASC
LIMIT 10

## Pattern 3: Jobs by Technology
Use when query asks WHICH jobs use a specific technology
CRITICAL: Use CONTAINS because technology fields have comma-separated values

Example: "Which jobs use Python as a top language?"
MATCH (j:Job)
WHERE j.top_language CONTAINS 'Python'
RETURN j.name AS job_name, j.median_comp AS salary
ORDER BY j.median_comp DESC

Example: "Jobs that use React"
MATCH (j:Job)
WHERE j.top_webframe CONTAINS 'React'
RETURN j.name AS job_name, j.median_comp AS salary
ORDER BY j.median_comp DESC

Example: "Which jobs use PostgreSQL?"
MATCH (j:Job)
WHERE j.top_database CONTAINS 'PostgreSQL'
RETURN j.name AS job_name, j.median_comp AS salary
ORDER BY j.median_comp DESC

Example: "Jobs using AWS"
MATCH (j:Job)
WHERE j.top_platform CONTAINS 'AWS'
RETURN j.name AS job_name, j.median_comp AS salary
ORDER BY j.median_comp DESC

Example: "Which jobs use both Python and PostgreSQL?"
MATCH (j:Job)
WHERE j.top_language CONTAINS 'Python' 
  AND j.top_database CONTAINS 'PostgreSQL'
RETURN j.name AS job_name, j.median_comp AS salary
ORDER BY j.median_comp DESC

## Pattern 4: Salary/Pay Comparison Queries
Use when query asks about salary increases or better-paying jobs

Example: "What jobs pay more than Engineering manager?"
MATCH (current:Job {{name: 'Engineering manager'}})-[r:RELATED_TO]->(next:Job)
WHERE next.median_comp > current.median_comp
RETURN next.name AS job_name, 
       next.median_comp - current.median_comp AS salary_increase,
       next.median_comp AS new_salary
ORDER BY salary_increase DESC
LIMIT 10
                                                        
## Pattern 5: Experience-based Queries
Use when query asks about jobs by experience level

Example: "What jobs require less than 3 years experience?"
MATCH (j:Job)
WHERE j.median_workexp <= 3
RETURN j.name AS job_name, j.median_workexp AS years_required, j.median_comp AS salary
ORDER BY j.median_comp DESC

Example: "Entry-level jobs" (0-2 years)
MATCH (j:Job)
WHERE j.median_workexp <= 2
RETURN j.name AS job_name, j.median_workexp AS years_required, j.median_comp AS salary
ORDER BY j.median_comp DESC

## Pattern 6: Combined Filters
Use when query has multiple conditions

Example: "High-paying Python jobs with less than 5 years experience"
MATCH (j:Job)
WHERE j.top_language CONTAINS 'Python' 
  AND j.median_workexp <= 5 
  AND j.median_comp > 80000
RETURN j.name AS job_name, 
       j.median_comp AS salary,
       j.median_workexp AS experience_years
ORDER BY j.median_comp DESC
                                                        
## Pattern 7: Personalized Career Recommendations
Use when query contains user profile information: <USER_PROFILE:job_title|skills>
This pattern returns related jobs WITH their required skills

Example: "Generate career recommendation <USER_PROFILE:Data or business analyst|Databricks SQL,Python>"
MATCH (current:Job {{name: 'Data or business analyst'}})-[r:RELATED_TO]->(related:Job)
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

KEYWORD MAPPING:
- "skills/technologies/tools/tech stack" for a specific job → Pattern 1 (return properties)
- "salary/compensation/pay" for a specific job → Pattern 1 (return median_comp)
- "experience/years" for a specific job → Pattern 1 (return median_workexp)
- "similar/related/transitions/career path" from a specific job → Pattern 2 (use RELATED_TO)
- "which jobs use [technology]" → Pattern 3 (use CONTAINS)
- "high-paying/better-paying" jobs → Pattern 4 (use WHERE with median_comp)
- "entry-level/junior/senior" → Pattern 5 (use WHERE with median_workexp)
- "generate my career recommendation" → Pattern 7 (use <USER_PROFILE:...>)


COMMON TECHNOLOGY NAMES (case-sensitive):
Languages: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, R, SQL
Databases: PostgreSQL, MySQL, MongoDB, Redis, SQLite, Oracle, Microsoft SQL Server, Cassandra, DynamoDB
Platforms: AWS, Azure, Google Cloud Platform, Linux, Docker, Kubernetes, Heroku, Jenkins
Frameworks: React, Angular, Vue, Django, Flask, Spring, Express, Laravel, Rails, .NET

User Query: {query}

""")


# Prompt used for formatting natural language answers from Cypher results
qa_generation_prompt = PromptTemplate(
    input_variables=["context", "question"],  
    template="""You are a data formatter. Your ONLY job is to present the database query results clearly.

=== QUERY RESULTS ===
{context}

=== USER QUESTION ===
{question}

=== YOUR INSTRUCTIONS ===

STEP 1: Look at the Query Results above. Does it contain data?
- If you see: [{{'job_name': 'something', 'salary': 12345.0}}, ...] → YOU HAVE DATA
- If you see: [] or no results → YOU HAVE NO DATA

STEP 2: Count how many items are in Query Results
- Count EVERY dictionary in the list
- You must present EXACTLY that many items in your response

STEP 3: Format your response

✅ IF YOU HAVE DATA:
Present ALL results in a numbered list. DO NOT SKIP ANY RESULTS.

Format:
"Here are the jobs that match your query:

1. [job_name] - $[salary with commas]
2. [job_name] - $[salary with commas]
3. [job_name] - $[salary with commas]
...
[continue for EVERY item in Query Results]"

❌ IF YOU HAVE NO DATA (empty list [] only):
Say: "I don't have that information in the database."

=== CRITICAL RULES ===
1. ALWAYS present data if Query Results contains any job names/salaries
2. NEVER say "I don't have information" when you can see data in Query Results
3. Present EVERY SINGLE result - if there are 22 results, show all 22
4. DO NOT summarize or show only a few examples - show COMPLETE list
5. DO NOT truncate the list - include every item from first to last
6. Count the items in Query Results and make sure your numbered list has the same count
7. Do not add explanations - just present the numbered list

=== EXAMPLE 1: Small Result Set ===
Question: "Which jobs use both C++ and React?"
Query Results: [{{'job_name': 'Financial analyst or engineer', 'salary': 146500.0}}, {{'job_name': 'Developer, game or graphics', 'salary': 70794.0}}]

CORRECT Response:
"Here are the jobs that match your query:

1. Financial analyst or engineer - $146,500
2. Developer, game or graphics - $70,794"

=== EXAMPLE 2: Large Result Set ===
If Query Results has 22 items, your response must have 22 numbered items. DO NOT show only 3 and stop.

=== EXAMPLE 3: Asking about salary/pay differences ===
Response must have all job_name, its new_salary and its salary_increase. 

NOW FORMAT THE RESULTS ABOVE - INCLUDE EVERY SINGLE ITEM:
"""
)


# Build the LangChain GraphCypherQAChain (LLM → Cypher → Neo4j → LLM formatting)
career_cypher_chain = GraphCypherQAChain.from_llm(
    cypher_llm=ChatOpenAI(model=CAREER_CYPHER_MODEL, temperature=0),
    qa_llm=ChatOpenAI(model=CAREER_QA_MODEL, temperature=0),
    graph=graph,
    verbose=True,  # Print steps to console for debugging
    qa_prompt=qa_generation_prompt, # Format answers using custom rules
    cypher_prompt=cypher_generation_prompt, # Generate Cypher queries
    validate_cypher=True,  # Ensures queries follow proper syntax
    allow_dangerous_requests=True, # Allows LLM to generate complex queries
    top_k=50, # Limit returned results
)

print("✅ Career Skill Graph QA Chain initialized successfully.")


# ============================================
# COURSE RECOMMENDATION CHAIN (Supabase)
# ============================================
# Optionally disable the course recommender for local/dev environments 
if os.getenv("DISABLE_COURSE_RECOMMENDER", "0").lower() in ("1", "true", "yes"):
    print("Course recommender disabled by DISABLE_COURSE_RECOMMENDER environment variable.")
    supabase_vector_store = None
    qa_chain = None
else:
    # Try initializing PGVector + embeddings
    try:
        # SentenceTransformer embeddings for vector search
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

        # Vector store that connects to Supabase Postgres with pgvector
        print("Connecting to PGVector store...")
        supabase_vector_store = PGVector(
            connection=SUPABASE_CONNECTION_STRING,
            embeddings=embeddings,
            collection_name="course_embeddings", # Table name in Supabase
        )

        # Prompt template used for course recommendation formatting
        course_template = """You are a helpful course recommender system for an online learning platform.

        Based on the following course information, recommend the most relevant courses to the user.

        IMPORTANT: Each course in the context has a 'course_url' in its metadata. You MUST 
        use the EXACT course_url provided - DO NOT make up or modify URLs.

        For each recommended course, format your output as:
        - Course title (use the exact title from metadata)
        - Course URL (use the EXACT course_url from metadata)

        Output as a clean numbered list.

        Course Information:
        {context}

        If no relevant courses are found, politely let the user know and suggest they try a different search term.

        Remember: Use ONLY the actual course_url values from the metadata. Never generate example.com or placeholder URLs.
        """

        # System-level instructions for formatting outputs
        system_prompt = SystemMessagePromptTemplate(
            prompt=PromptTemplate(input_variables=["context"], template=course_template)
        )

        # Pass user query into the chain
        human_prompt = HumanMessagePromptTemplate(
            prompt=PromptTemplate(input_variables=["question"], template="{question}")
        )

        # Combine system + user prompt
        review_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

        # Build RetrievalQA chain (LLM + vector search)
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model=CAREER_QA_MODEL, temperature=0),
            chain_type="stuff",
            retriever=supabase_vector_store.as_retriever(
                search_kwargs={"k": 5}  # Retrieve top 5 most relevant courses
            ),
            return_source_documents=True,  # Include course URLs in output
        )
        # Override chain prompt with our custom template
        qa_chain.combine_documents_chain.llm_chain.prompt = review_prompt

        print("✅ Course Recommender Chain initialized successfully.")
        
    # On failure, disable the course recommender gracefully
    except Exception as e:
        print("Warning: failed to initialize course recommender:", repr(e))
        supabase_vector_store = None
        qa_chain = None
    # Duplicate fail-safe (intentional repetition preserved)
    except Exception as e:
        print("Warning: failed to initialize course recommender:", repr(e))
        supabase_vector_store = None
        qa_chain = None