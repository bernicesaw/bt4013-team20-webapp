"""
Test Dataset for RAGAS Evaluation
Contains test cases for all three components of the career chatbot
"""

# ============================================
# COURSE RECOMMENDATION TEST CASES
# ============================================
COURSE_RECOMMENDATION_TEST_SET = [
    # Popular programming languages
    {
        "question": "Python programming courses",
        "ground_truth": "Courses covering Python programming fundamentals and advanced topics",
    },
    
    # Web frameworks
    {
        "question": "React courses for beginners",
        "ground_truth": "Beginner-friendly courses on React framework for frontend development",
    },
    
    # Databases
    {
        "question": "PostgreSQL database courses",
        "ground_truth": "Courses focused on PostgreSQL relational database management",
    },
    
    # Cloud platforms
    {
        "question": "Learn Google Cloud Platform",
        "ground_truth": "Courses teaching Google Cloud Platform services and tools",
    },
    
    # Data Science & ML
    {
        "question": "Machine learning courses",
        "ground_truth": "Courses covering machine learning algorithms, concepts, and applications",
    },
    
    # DevOps & Tools
    {
        "question": "Docker courses",
        "ground_truth": "Courses on Docker containerization platform",
    },
    
    # Edge cases
    {
        "question": "Cooking classes",
        "ground_truth": "No tech courses available - non-technical topic",
    },
]


# ============================================
# CAREER GRAPH TEST CASES (Neo4j)
# ============================================
CAREER_GRAPH_TEST_SET = [
    # Skills queries
    {
        "question": "What skills does a Data scientist need?",
        "ground_truth": "Skills including PostgreSQL, SQLite, MySQL, Microsoft SQL Server, MongoDB, Python, SQL, Bash/Shell (all shells), HTML/CSS, R, Docker, Pip, Amazon Web Services (AWS), Microsoft Azure, Google Cloud, cFastAPI, Flask, Node.js, React, Django",
    },
    
    # Salary queries
    {
        "question": "What is the median salary for a Data scientist?",
        "ground_truth": "87011",
    },
    
    # Experience queries
    {
        "question": "How many years of experience does a Data or business analyst typically have?",
        "ground_truth": "8",
    },
    
    # Jobs by technology
    {
        "question": "Jobs that use Angular",
        "ground_truth": "Front-end Developer, QA or Test Developer, Support Engineer or Analyst, DevOps Engineer or Professional, Product Manager, Software or Solutions Architect, Project Manager",
    },
    
    
    # Salary comparisons
    {
        "question": "What jobs pay more than Engineering manager?",
        "ground_truth": "Financial analyst or engineer",
    },
    
    # Experience-based
    {
        "question": "Jobs requiring less than 7 years experience",
        "ground_truth": "Academic researcher",
    },
]
