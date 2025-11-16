"""
Standalone RAGAS evaluation for Career Chatbot
Evaluates both course recommendations and career graph queries
Run in separate venv_evaluation environment
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_community.graphs import Neo4jGraph
from langchain.chains import RetrievalQA, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

# run the test dataset in the results folder
from test_dataset import COURSE_RECOMMENDATION_TEST_SET, CAREER_GRAPH_TEST_SET

# Load environment variables (DB credentials, API keys, model names, etc.)
load_dotenv()


# ============================================
# SETUP FUNCTIONS
# ============================================

def setup_course_chain():
    # Fetch connection string + model from environment
    """Setup course recommendation chain"""
    SUPABASE_CONNECTION_STRING = os.getenv("SUPABASE_POOLER_URL")
    CAREER_QA_MODEL = os.getenv("CAREER_AGENT_MODEL")

    # Initialize transformer embeddings for vector retrieval
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Connect to Supabase Postgres vector store
    supabase_vector_store = PGVector(
        connection=SUPABASE_CONNECTION_STRING,
        embeddings=embeddings,
        collection_name="course_embeddings",
    )
    
    # same prompt from chains.py
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
    
    system_prompt = SystemMessagePromptTemplate(
        prompt=PromptTemplate(input_variables=["context"], template=course_template)
    )
    human_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(input_variables=["question"], template="{question}")
    )
    review_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model=CAREER_QA_MODEL, temperature=0),
        chain_type="stuff",
        retriever=supabase_vector_store.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True,
    )
    qa_chain.combine_documents_chain.llm_chain.prompt = review_prompt
    
    return qa_chain


def setup_career_graph_chain():
    """Setup career graph chain"""
    
    # Initialize Neo4j graph connection using credentials from env
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )
    graph.refresh_schema()
    
    # same prompt from chains.py
    cypher_prompt = PromptTemplate.from_template("""
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
    
    # same prompt from chains.py
    qa_prompt = PromptTemplate(
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
    
    CAREER_QA_MODEL = os.getenv("CAREER_AGENT_MODEL")
    
    chain = GraphCypherQAChain.from_llm(
        cypher_llm=ChatOpenAI(model=CAREER_QA_MODEL, temperature=0),
        qa_llm=ChatOpenAI(model=CAREER_QA_MODEL, temperature=0),
        graph=graph,
        verbose=False,
        qa_prompt=qa_prompt,
        cypher_prompt=cypher_prompt,
        validate_cypher=True,
        allow_dangerous_requests=True,
        top_k=50,
    )
    
    return chain


# ============================================
# EVALUATION FUNCTIONS
# ============================================

def evaluate_course_recommendations():
    """Evaluate course recommendations"""
    
    print("=" * 70)
    print(" " * 15 + "EVALUATING: COURSE RECOMMENDATIONS")
    print("=" * 70)
    
    qa_chain = setup_course_chain()
    evaluation_data = []
    
    # Iterate over each test case
    for i, test_case in enumerate(COURSE_RECOMMENDATION_TEST_SET, 1):
        question = test_case['question']
        print(f"[{i}/{len(COURSE_RECOMMENDATION_TEST_SET)}] {question}")
        
        try:
            # Run chain inference for the question
            result = qa_chain.invoke({"query": question})
            
            # Extract retrieved documents for RAGAS context fields
            contexts = []
            if "source_documents" in result:
                for doc in result["source_documents"]:
                    title = doc.metadata.get('title', 'Untitled')
                    content = doc.page_content
                    contexts.append(f"Title: {title}\nDescription: {content}")
            
            answer = result.get("result", "")
            
            # Save data row for RAGAS evaluation
            evaluation_data.append({
                "question": question,
                "answer": answer,
                "contexts": contexts if contexts else ["No context"],
                "ground_truth": test_case.get("ground_truth", "")
            })
            
            print(f"    ✓ Retrieved {len(contexts)} courses")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            # Error handling: still append to evaluation_data
            evaluation_data.append({
                "question": question,
                "answer": f"Error: {str(e)}",
                "contexts": ["Error"],
                "ground_truth": test_case.get("ground_truth", "")
            })
    
    # Run RAGAS
    # Convert collected data into a HuggingFace dataset
    dataset = Dataset.from_list(evaluation_data)

    # Embeddings for RAGAS semantic comparisons
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("\n🚀 Running RAGAS evaluation...\n")
    
    # Run RAGAS metrics
    result = evaluate(
        dataset=dataset,
        metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
        llm=ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0),
        embeddings=embeddings,
    )
    
    return result.to_pandas()


def evaluate_career_graph():
    """Evaluate career graph queries"""
    
    print("\n" + "=" * 70)
    print(" " * 15 + "EVALUATING: CAREER GRAPH QUERIES")
    print("=" * 70)
    
    chain = setup_career_graph_chain()
    evaluation_data = []
    
    for i, test_case in enumerate(CAREER_GRAPH_TEST_SET, 1):
        question = test_case['question']
        print(f"[{i}/{len(CAREER_GRAPH_TEST_SET)}] {question}")
        
        try:
            # Execute graph query chain
            result = chain.invoke({"query": question})
            answer = result.get("result", str(result))
            
            # Append evaluation row
            evaluation_data.append({
                "question": question,
                "answer": answer,
                "contexts": [answer],
                "ground_truth": test_case.get("ground_truth", "")
            })
            
            print(f"    ✓ Answer length: {len(answer)} chars")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            evaluation_data.append({
                "question": question,
                "answer": f"Error: {str(e)}",
                "contexts": ["Error"],
                "ground_truth": test_case.get("ground_truth", "")
            })
    
    # Run RAGAS
    # Convert collected test cases into Dataset
    dataset = Dataset.from_list(evaluation_data)
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("\n🚀 Running RAGAS evaluation...\n")
    
    # Run RAGAS evaluation (career graph uses only 2 metrics)
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0),
        embeddings=embeddings,
    )
    
    return result.to_pandas()


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    print("\n" + "=" * 70)
    print(" " * 15 + "CAREER CHATBOT - RAGAS EVALUATION")
    print("=" * 70)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Evaluate course recommendations
    course_df = evaluate_course_recommendations()
    
    # Evaluate career graph
    graph_df = evaluate_career_graph()
    
    # Display results
    print("\n" + "=" * 70)
    print(" " * 25 + "RESULTS SUMMARY")
    print("=" * 70)
    
    print("\n📊 COURSE RECOMMENDATIONS:")
    print("-" * 70)
    for metric in ['context_precision', 'context_recall', 'faithfulness', 'answer_relevancy']:
        if metric in course_df.columns:
            print(f"  {metric.replace('_', ' ').title():.<50} {course_df[metric].mean():.3f}")
    
    print("\n📊 CAREER GRAPH QUERIES:")
    print("-" * 70)
    for metric in ['faithfulness', 'answer_relevancy']:
        if metric in graph_df.columns:
            print(f"  {metric.replace('_', ' ').title():.<50} {graph_df[metric].mean():.3f}")
    
    # Save results
    os.makedirs("results", exist_ok=True)
    
    course_df.to_csv("results/course_recommendations.csv", index=False)
    graph_df.to_csv("results/career_graph.csv", index=False)
    
    # Combined report
    report = f"""
{'=' * 70}
        CAREER CHATBOT - RAGAS EVALUATION REPORT
{'=' * 70}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

COURSE RECOMMENDATIONS ({len(course_df)} test cases)
  Context Precision:  {course_df['context_precision'].mean():.3f}
  Context Recall:     {course_df['context_recall'].mean():.3f}
  Faithfulness:       {course_df['faithfulness'].mean():.3f}
  Answer Relevancy:   {course_df['answer_relevancy'].mean():.3f}

CAREER GRAPH QUERIES ({len(graph_df)} test cases)
  Faithfulness:       {graph_df['faithfulness'].mean():.3f}
  Answer Relevancy:   {graph_df['answer_relevancy'].mean():.3f}

OVERALL
  Avg Faithfulness:     {(course_df['faithfulness'].mean() + graph_df['faithfulness'].mean()) / 2:.3f}
  Avg Answer Relevancy: {(course_df['answer_relevancy'].mean() + graph_df['answer_relevancy'].mean()) / 2:.3f}

{'=' * 70}
"""
    
    print(report)
    
     # Save full text report
    report_file = f"results/EVALUATION_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n💾 Results saved:")
    print(f"   - results/course_recommendations.csv")
    print(f"   - results/career_graph.csv")
    print(f"   - {report_file}")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
