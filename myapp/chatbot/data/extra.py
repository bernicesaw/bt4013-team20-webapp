from sentence_transformers import SentenceTransformer
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Manually define the courses
courses = [
    {
        "course_url": "https://www.coursera.org/projects/googlecloud-getting-started-with-redis-and-redisearch-vmk1o",
        "title": "Getting Started with Redis and RediSearch",
        "description_full": "This is a self-paced lab that takes place in the Google Cloud console. In this lab you will use Redis and RediSearch, an add-on module that enables full-text search and secondary indexing in Redis, to install and run a Redis instance, import example hashes, index them with RediSearch, and query them."
    },
    {
        "course_url": "https://www.coursera.org/learn/aws-getting-started-with-amazon-rds-for-mariadb",
        "title": "Getting Started with Amazon RDS for MariaDB",
        "description_full": "With Amazon Relational Database Service (Amazon RDS) for MariaDB, you can run the MariaDB open-source database engine on the Amazon Web Services (AWS) relational database service, Amazon RDS. In this course, you will learn the benefits and technical concepts of Amazon RDS for MariaDB. If you are new to the service, you will learn how to start using Amazon RDS for MariaDB through a demonstration using the AWS Management Console. You will learn about the native architecture and how the built-in features can help you simplify scaling and management of your database solution."
    }
]

# Generate and store embeddings for each course
for course in courses:
    # Combine the title and description to create the text for embedding
    text_to_embed = f"{course['title']} {course['description_full']}"
    
    # Generate the embedding for the text
    embedding = model.encode(text_to_embed).tolist()

    # Insert the course with its embedding into the course_embeddings table
    response = supabase.table("course_embeddings").insert({
        "course_url": course["course_url"],
        "embedding": embedding
    }).execute()

print('success')