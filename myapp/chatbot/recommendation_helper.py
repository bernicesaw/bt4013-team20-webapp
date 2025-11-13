"""
Helper functions for personalized career recommendations
Fetches user profile and generates recommendations with courses
"""
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from langchain_postgres.vectorstores import PGVector
from langchain_community.embeddings import SentenceTransformerEmbeddings
import psycopg2
from accounts.models import Profile 

load_dotenv()


def fetch_user_profile(user_id: int) -> Optional[Dict[str, any]]:
    """
    Fetch user's job_title and skills from accounts_profile table using Django ORM
    
    Args:
        user_id: The authenticated user's ID (integer)
    
    Returns:
        {"job_title": "Data or business analyst", "skills": ["Databricks SQL", "Python"]}
    """
    try:
        # Use Django ORM instead of raw SQL
        user_profile = Profile.objects.get(user=user_id)
        
        # Extract job title
        job_title = user_profile.job_title
        
        # Extract skills - it's already a JSONField (list)
        skills = user_profile.skills
        if not isinstance(skills, list):
            skills = []
        
        # Clean up skills list
        skills = [s for s in skills if s]  # Remove empty strings
        
        print(f"✅ Fetched profile: job='{job_title}', skills={skills}")
        return {
            "job_title": job_title,
            "skills": [s.lower().strip() for s in skills]  # Normalize to lowercase
        }
        
    except Profile.DoesNotExist:
        print(f"⚠️ No profile found for user_id: {user_id}")
        return None
            
    except Exception as e:
        print(f"❌ Error fetching user profile: {e}")
        return None
    

def find_missing_skills(user_skills: List[str], job_skills_dict: Dict[str, str]) -> List[str]:
    # Normalize user skills to lowercase for comparison
    user_skills_normalized = [skill.lower() for skill in user_skills]
    
    # Extract all job skills from the dict
    all_job_skills = []
    for field, skills_str in job_skills_dict.items():
        if skills_str:
            # Split comma-separated skills
            skills_list = [s.strip() for s in skills_str.split(',')]
            all_job_skills.extend(skills_list)
    
    # Find missing skills (case-insensitive comparison)
    missing = []
    for job_skill in all_job_skills:
        # Check if this job skill is NOT in user's skills
        if not any(user_skill in job_skill.lower() or job_skill.lower() in user_skill 
                   for user_skill in user_skills_normalized):
            missing.append(job_skill)
    
    # Remove duplicates while preserving order
    seen = set()
    missing_unique = []
    for skill in missing:
        if skill.lower() not in seen:
            seen.add(skill.lower())
            missing_unique.append(skill)
    
    return missing_unique


# use vector search for courses
# def find_course_for_skill(skill: str, vector_store: PGVector, max_results: int = 1) -> Optional[Dict[str, str]]:
#     try:
#         # Search for courses related to this skill
#         docs = vector_store.similarity_search(
#             query=f"{skill}",
#             k=max_results
#         )
        
#         if docs:
#             doc = docs[0]
#             return {
#                 "title": doc.metadata.get('title', f'{skill} Course'),
#                 "url": doc.metadata.get('course_url', '#')
#             }
#         else:
#             return None
            
#     except Exception as e:
#         print(f"❌ Error finding course for {skill}: {e}")
#         return None

# Define your skill-to-course mapping
SKILL_COURSE_MAPPING = {
    # Programming Languages
    "python": {"title": "Introduction to Python Programming", "url": "https://www.coursera.org/learn/python-programming-intro"},
    "java": {"title": "Learn Java", "url": "https://www.codecademy.com/learn/learn-java"},
    "javascript": {"title": "Learn JavaScript: Fundamentals", "url": "https://www.codecademy.com/learn/learn-javascript-fundamentals/"},
    "r": {"title": "Getting Started with R", "url": "https://www.coursera.org/projects/getting-started-with-r"},
    "c++": {"title": "Introduction to C++", "url": "https://www.coursera.org/learn/introduction-to-c"},
    "sql": {"title": "Intro to SQL", "url": "https://www.codecademy.com/learn/intro-to-sql"},
    "kotlin": {"title": "Learn Kotlin: Introduction", "url": "https://www.codecademy.com/learn/learn-kotlin-introduction"},
    "swift": {"title": "Learn Swift: Introduction", "url": "https://www.codecademy.com/learn/learn-swift-introduction"},
    "html/css": {"title": "Learn HTML: Fundamentals", "url": "https://www.codecademy.com/learn/learn-html-fundamentals"},
    "bash/shell (all shells)": {"title": "Introduction to Bash Shell Scripting", "url": "https://www.coursera.org/projects/introduction-to-bash-shell-scripting?utm_medium=sem&utm_source=gg&utm_campaign=b2c_apac_x_multi_ftcof_career-academy_cx_dr_bau_gg_pmax_gc_sg_all_m_hyb_25-04_x&campaignid=22449465350&adgroupid=&device=c&keyword=&matchtype=&network=x&devicemodel=&creativeid=&assetgroupid=6568546196&targetid=&extensionid=&placement=&gad_source=1&gad_campaignid=22442997015&gbraid=0AAAAADdKX6ZNc5UZe4An4dxRRTjS8O73C&gclid=CjwKCAiA_dDIBhB6EiwAvzc1cAUy6-bOI08tLW3NR2ietPh5nl1X7UDZYQ9fkMurUZh8IqJ24dsIuhoC3zkQAvD_BwE"},
    "html/css": {"title": "Learn TypeScript", "url": "https://www.codecademy.com/learn/learn-typescript"},


    # Databases
    "mysql": {"title": "Introduction to Structured Query Language (SQL)", "url": "https://www.coursera.org/learn/intro-sql"},
    "postgresql": {"title": "Database Design and Basic SQL in PostgreSQL", "url": "https://www.coursera.org/learn/database-design-postgresql"},
    "mongodb": {"title": "Learn MongoDB", "url": "https://www.codecademy.com/learn/learn-mongodb"},
    "redis": {"title": "Getting Started with Redis and RediSearch", "url": "https://www.coursera.org/projects/googlecloud-getting-started-with-redis-and-redisearch-vmk1o"},
    "sqlite": {"title": "Learn Node-SQLite", "url": "https://www.codecademy.com/learn/learn-node-sqlite"},
    "cloud firestore": {"title": "Getting started with Firebase Cloud Firestore", "url": "https://www.coursera.org/projects/googlecloud-getting-started-with-firebase-cloud-firestore-f6q7j"},
    "elasticsearch": {"title": "Foundations of Elasticsearch", "url": "https://www.coursera.org/learn/packt-foundations-of-elasticsearch-uohrj"},
    "pip": {"title": "Programming for Everybody (Getting Started with Python)", "url": "https://www.coursera.org/learn/python"},
    "jquery": {"title": "Learn jQuery", "url": "https://www.codecademy.com/learn/learn-jquery"},
    "spring boot": {"title": "Learn Spring", "url": "https://www.codecademy.com/learn/learn-spring"},
    "fastapi": {"title": "Introduction to FastAPI framework", "url": "https://www.coursera.org/projects/introduction-to-fastapi-framework"},
    "next.js": {"title": "Learn Next.js", "url": "https://www.codecademy.com/learn/learn-next-js"},
    "asp.net core": {"title": "Learn ASP.NET", "url": "https://www.codecademy.com/learn/learn-asp-net"},

    # Cloud Platforms
    "aws": {"title": "AWS Cloud Technical Essentials", "url": "https://www.coursera.org/learn/aws-cloud-technical-essentials"},
    "azure": {"title": "Introduction to Microsoft Azure Cloud Services", "url": "https://www.coursera.org/learn/microsoft-azure-cloud-services"},
    "google cloud": {"title": "Google Cloud Fundamentals: Core Infrastructure", "url": "https://www.coursera.org/learn/gcp-fundamentals"},

    # Web Frameworks
    "react": {"title": "Learn React: Introduction", "url": "https://www.codecademy.com/learn/learn-react-introduction"},
    "angular": {"title": "Intro to Angular", "url": "https://www.codecademy.com/learn/intro-to-angular"},
    "vue.js": {"title": "Learn Vue.js", "url": "https://www.codecademy.com/learn/learn-vue-js"},
    "django": {"title": "Django for Everybody Specialization", "url": "https://www.coursera.org/specializations/django"},
    "flask": {"title": "Learn Flask: Fundamentals", "url": "https://www.codecademy.com/learn/learn-flask-fundamentals"},
    "express": {"title": "Learn Express", "url": "https://www.codecademy.com/learn/learn-express"},
    "node.js": {"title": "Learn Node.js: Fundamentals", "url": "https://www.codecademy.com/learn/learn-nodejs-fundamentals"},
    
    # Platforms & Tools
    "firebase realtime database": {"title": "Learn Firebase", "url": "https://www.coursera.org/learn/learn-firebase"},
    "kubernetes": {"title": "Kubernetes for Beginners", "url": "https://www.coursera.org/learn/packt-kubernetes-for-beginners-pj7v5"},
    "docker": {"title": "Docker for Beginners with Hands-on labs", "url": "https://www.coursera.org/learn/docker-for-the-absolute-beginner"},
    "terraform": {"title": "Terraform for absolute beginners", "url": "https://www.coursera.org/projects/terraform-for-absolute-beginners"},
    "npm": {"title": "NPM - Node package manager", "url": "hhttps://www.udemy.com/course/npm-node-package-manager-course/"},

    # Data Science & ML
    "tensorflow": {"title": "Introduction to TensorFlow for Artificial Intelligence, Machine Learning, and Deep Learning", "url": "https://www.coursera.org/learn/introduction-tensorflow"},
    "pytorch": {"title": "Introduction to Neural Networks and PyTorch", "url": "https://www.coursera.org/learn/deep-neural-networks-with-pytorch"},
    "scikit-learn": {"title": "Introduction to Data Science and scikit-learn in Python", "url": "https://www.coursera.org/learn/data-science-and-scikit-learn-in-python"},
    "pandas": {"title": "Learn Data Analysis with Pandas", "url": "https://www.codecademy.com/learn/data-processing-pandas"},
    "numpy": {"title": "Intro to NumPy", "url": "https://www.coursera.org/learn/packt-intro-to-numpy-ftdg2"},
    
    # Game Development
    "unity": {"title": "Learn Unity 3D for Absolute Beginners", "url": "https://www.udemy.com/course/learnunity3d/"},
    "unreal engine": {"title": "Unreal Engine Fundamentals", "url": "https://www.coursera.org/learn/unreal-engine-fundamentals"}
}

def find_course_for_skill(skill: str, vector_store: PGVector = None, max_results: int = 1) -> Optional[Dict[str, str]]:
    """
    Find a pre-defined course for a given skill.
    Only does exact matching (case-insensitive).
    """
    # Normalize the skill for matching
    skill_lower = skill.lower().strip()
    
    # Try exact match only
    if skill_lower in SKILL_COURSE_MAPPING:
        return SKILL_COURSE_MAPPING[skill_lower]
    
    # If no exact match found, return a generic course suggestion
    return {
        "title": f"Learn {skill} - Search on Coursera",
        "url": f"https://www.coursera.org/search?query={skill.replace(' ', '%20')}"
    }

def format_recommendation_output(
    user_job: str,
    recommendations: List[Dict],
    user_skills: List[str],
    vector_store: PGVector = None  # Keep for compatibility but not used
) -> str:
    output = f"For your job as a **{user_job}**, here are the top 3 recommended career pathways:\n\n"
    
    for i, job_data in enumerate(recommendations, 1):
        job_name = job_data.get('job_name', 'Unknown Job')
        salary = job_data.get('salary', 'N/A')
        experience = job_data.get('experience', 'N/A')
        
        # Get all skills for this job
        job_skills = {
            'language': job_data.get('language', ''),
            'database': job_data.get('database', ''),
            'platform': job_data.get('platform', ''),
            'framework': job_data.get('framework', '')
        }
        
        # Find missing skills
        missing_skills = find_missing_skills(user_skills, job_skills)
        
        # Format job header
        output += f"### {i}. {job_name}\n"
        output += f"- **Salary**: ${salary:,.0f}\n" if isinstance(salary, (int, float)) else f"- **Salary**: {salary}\n"
        output += f"- **Experience**: {experience} years\n\n"
        
        if missing_skills:
            output += "**Skills to learn:**\n"
            
            # For each missing skill, find a course
            for skill in missing_skills[:5]:  # Limit to 5 missing skills per job
                course = find_course_for_skill(skill)  # No need to pass vector_store
                
                if course:
                    output += f"- {skill}: [{course['title']}]({course['url']})\n"
                else:
                    output += f"- {skill}: (No course found)\n"
        else:
            output += "**Great news!** You already have all the key skills for this role.\n"
        
        output += "\n"
    
    return output

# vector search version
# def format_recommendation_output(
#     user_job: str,
#     recommendations: List[Dict],
#     user_skills: List[str],
#     vector_store: PGVector
# ) -> str:
#     output = f"For your job as a **{user_job}**, here are the top 3 recommended career pathways:\n\n"
    
#     for i, job_data in enumerate(recommendations, 1):
#         job_name = job_data.get('job_name', 'Unknown Job')
#         salary = job_data.get('salary', 'N/A')
#         experience = job_data.get('experience', 'N/A')
        
#         # Get all skills for this job
#         job_skills = {
#             'language': job_data.get('language', ''),
#             'database': job_data.get('database', ''),
#             'platform': job_data.get('platform', ''),
#             'framework': job_data.get('framework', '')
#         }
        
#         # Find missing skills
#         missing_skills = find_missing_skills(user_skills, job_skills)
        
#         # Format job header
#         output += f"### {i}. {job_name}\n"
#         output += f"- **Salary**: ${salary:,.0f}\n" if isinstance(salary, (int, float)) else f"- **Salary**: {salary}\n"
#         output += f"- **Experience**: {experience} years\n\n"
        
#         if missing_skills:
#             output += "**Skills to learn:**\n"
            
#             # For each missing skill, find a course
#             for skill in missing_skills[:5]:  # Limit to 5 missing skills per job
#                 course = find_course_for_skill(skill, vector_store)
                
#                 if course:
#                     output += f"- {skill}: [{course['title']}]({course['url']})\n"
#                 else:
#                     output += f"- {skill}: (No course found)\n"
#         else:
#             output += "**Great news!** You already have all the key skills for this role.\n"
        
#         output += "\n"
    
#     return output