"""
Job Title Normalization Utilities
Handles fuzzy matching and synonym mapping for career graph queries
"""
from rapidfuzz import process, fuzz
from typing import Optional, List, Tuple

class EnhancedJobTitleNormalizer:
    """Enhanced normalizer with synonym dictionary + fuzzy matching"""
    
    # Common synonyms and variations
    # Maps user input (lowercase) -> Database name (exact from Neo4j)
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
        
        # AI/ML roles (UPDATED)
        "ml engineer": "AI/ML engineer",
        "machine learning engineer": "AI/ML engineer",
        "ai engineer": "AI/ML engineer",
        "artificial intelligence engineer": "AI/ML engineer",
        "ai developer": "Developer, AI apps or physical AI",
        "ai app developer": "Developer, AI apps or physical AI",
        "physical ai developer": "Developer, AI apps or physical AI",
        "applied scientist": "Applied scientist",
        
        # Cloud/Infrastructure (UPDATED)
        "cloud engineer": "Cloud infrastructure engineer",
        "cloud infrastructure": "Cloud infrastructure engineer",
        "infrastructure engineer": "Cloud infrastructure engineer",
        "sysadmin": "System administrator",
        "sys admin": "System administrator",
        "system admin": "System administrator",
        "devops": "DevOps engineer or professional",
        "devops engineer": "DevOps engineer or professional",
        "devops professional": "DevOps engineer or professional",
        
        # Database (UPDATED)
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
        "pm": "Product manager",  # Most common PM abbreviation
        "product manager": "Product manager",
        "engineering manager": "Engineering manager",
        "eng manager": "Engineering manager",
        "em": "Engineering manager",
        
        # Security (NEW)
        "security": "Cybersecurity or InfoSec professional",
        "cybersecurity": "Cybersecurity or InfoSec professional",
        "infosec": "Cybersecurity or InfoSec professional",
        "security engineer": "Cybersecurity or InfoSec professional",
        "security professional": "Cybersecurity or InfoSec professional",
        
        # Support (NEW)
        "support engineer": "Support engineer or analyst",
        "support analyst": "Support engineer or analyst",
        "customer support": "Support engineer or analyst",
        
        # Design (NEW)
        "ux": "UX, Research Ops or UI design professional",
        "ui": "UX, Research Ops or UI design professional",
        "ux designer": "UX, Research Ops or UI design professional",
        "ui designer": "UX, Research Ops or UI design professional",
        "designer": "UX, Research Ops or UI design professional",
        "ux researcher": "UX, Research Ops or UI design professional",
        
        # Executive/Leadership (NEW)
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
        
        # Architecture (NEW)
        "architect": "Architect, software or solutions",
        "software architect": "Architect, software or solutions",
        "solutions architect": "Architect, software or solutions",
        "solution architect": "Architect, software or solutions",
        
        # Finance (NEW)
        "financial analyst": "Financial analyst or engineer",
        "financial engineer": "Financial analyst or engineer",
        "quant": "Financial analyst or engineer",
    }

    def __init__(self, graph):
        """Initialize with Neo4j graph connection"""
        self.graph = graph
        self.job_names = self._fetch_all_job_names()
        print(f"✅ Loaded {len(self.job_names)} job titles from database")

    def _fetch_all_job_names(self) -> List[str]:
        """Fetch all unique job names from Neo4j"""
        query = "MATCH (j:Job) RETURN DISTINCT j.name AS name"
        result = self.graph.query(query)
        return [record['name'] for record in result]
    
    def normalize(self, user_input: str, threshold: int = 75) -> Optional[str]:
        """
        Normalize with synonym checking first, then fuzzy matching
        
        Args:
            user_input: Raw job title from user
            threshold: Minimum similarity score for fuzzy matching
            
        Returns:
            Exact job name from database, or None if no match
        """
        if not user_input:
            return None
        
        # Clean and lowercase for synonym matching
        cleaned = user_input.strip().lower()
        
        # Check exact synonym match first (fastest)
        if cleaned in self.SYNONYMS:
            return self.SYNONYMS[cleaned]
        
        # Try partial synonym matching (check if any synonym is in the input)
        for synonym, db_name in self.SYNONYMS.items():
            if synonym in cleaned or cleaned in synonym:
                return db_name
        
        # Fall back to fuzzy matching on original case-preserved input
        best_match = process.extractOne(
            user_input.strip(),
            self.job_names,
            scorer=fuzz.token_sort_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0]  # Return the matched job name
        
        return None

    

# # testing
# if __name__ == "__main__":
#     """
#     Quick standalone test for job title normalization.
#     Run with:
#         python job_title_normalizer.py
#     Make sure your .env file has:
#         NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
#     """

#     import os
#     from dotenv import load_dotenv
#     from langchain_community.graphs import Neo4jGraph

#     load_dotenv()

#     # --- Connect to Neo4j ---
#     graph = Neo4jGraph(
#         url=os.getenv("NEO4J_URI"),
#         username=os.getenv("NEO4J_USERNAME"),
#         password=os.getenv("NEO4J_PASSWORD"),
#     )

#     # --- Instantiate your normalizer ---
#     normalizer = EnhancedJobTitleNormalizer(graph)

#     # --- Test queries ---
#     test_inputs = [
#         "backend dev",
#         "frontend developer",
#         "ml engineer",
#         "ai app developer",
#         "data sci",
#         "devops",
#         "cloud infra",
#         "ux researcher",
#         "business analyst",
#         "random title",
#     ]

#     print("\n🔍 Testing Job Title Normalizer with Live Neo4j Connection:\n")
#     for input_str in test_inputs:
#         normalized, feedback = normalizer.normalize_with_feedback(input_str)
#         print(f"Input: {input_str:<25} → Normalized: {normalized}")
#         print(f"   Feedback: {feedback}\n")
