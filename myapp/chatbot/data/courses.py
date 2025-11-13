from sentence_transformers import SentenceTransformer
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Fetch all courses from the "all_courses" table
courses = supabase.table("all_courses").select("*").execute().data

# Generate and store embeddings for each course
for course in courses:
    # Combine title and description for embedding
    text_to_embed = f"{course['title']} {course['description_full']}"
    
    # Generate the embedding (384-dimensional vector)
    embedding = model.encode(text_to_embed).tolist()

    # Insert the course and its embedding into the "course_embeddings" table
    supabase.table("course_embeddings").insert({
        "course_url": course["url"],
        "embedding": embedding
    }).execute()

print("Courses inserted successfully.")
