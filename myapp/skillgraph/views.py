import json
import ast
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import StackoverflowJobs2025, AccountsProfile  # Assuming Users is your accounts_profile model
from django.db.models import Min, Max

from django.db.models import Q
import numpy as np
from sentence_transformers import SentenceTransformer

from .models import CoursesWithEmbeddings  # NEW model import

# --- Helpers for "Top 3 Easiest Transitions" ---

def _norm_set(v):
    """Normalize skills that may come as JSON, list or CSV string -> lowercase set."""
    if v is None:
        return set()
    if isinstance(v, (list, tuple, set)):
        return {str(x).strip().lower() for x in v if str(x).strip()}
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return set()
        # try JSON-list first
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return {str(x).strip().lower() for x in parsed if str(x).strip()}
        except Exception:
            pass
        # fallback: CSV
        return {s.strip().lower() for s in v.split(",") if s.strip()}
    return set()

def _user_skill_set_from_profile(profile):
    """Profile.skills is JSON in your model. Make it a normalized set."""
    return _norm_set(getattr(profile, "skills", None))

def _job_skill_set(job):
    """Union skills across your four JSON columns in StackoverflowJobs2025."""
    s = set()
    for col in ("top_language", "top_database", "top_platform", "top_framework"):
        s |= _norm_set(getattr(job, col, None))
    return s

def _edge_from_user_to_job(user_set, job, source_title):
    req = _job_skill_set(job)
    if not req:
        return None
    overlap = user_set & req
    missing = req - user_set
    if not overlap:      # optional: skip jobs with zero overlap
        return None
    title = getattr(job, "job", None) or getattr(job, "job_title", None) or "Unknown"
    edge = {
        "source": source_title or "current_role",
        "target": title,
        "missing": sorted(missing),
        "overlap": sorted(overlap),
        "missing_count": len(missing),
        "overlap_count": len(overlap),
    }
    # Numeric difficulty (lower = easier). Keep tie-breakers consistent with your graph:
    #   1) fewer missing, 2) more overlap, 3) alphabetical title
    edge["difficulty"] = edge["missing_count"] + max(0, 50 - edge["overlap_count"]) * 1e-6
    return edge


# --- 1. Jaccard Similarity (Unchanged) ---
def jaccard_similarity(set_a, set_b):
    """Calculates the Jaccard similarity between two sets."""
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0

# --- 2. NEW Helper: Get User's Skill Set ---
def get_user_skill_set(user_model):
    """
    Parses the 'skills' field from the user model (accounts_profile).
    Handles list, JSON string, or comma-separated string.
    """
    skills_set = set()
    skill_data = getattr(user_model, 'skills', None) # Safely get 'skills'
    
    if not skill_data:
        return skills_set
    
    if isinstance(skill_data, list):
        skills_set.update(skill_data)
    elif isinstance(skill_data, str):
        try: # Try JSON (e.g., "['Python', 'SQL']")
            parsed_data = json.loads(skill_data)
            if isinstance(parsed_data, list):
                skills_set.update(parsed_data)
                return skills_set
        except (json.JSONDecodeError, TypeError): pass
        
        try: # Try Python literal (e.g., "['Python', 'SQL']")
            parsed_data = ast.literal_eval(skill_data)
            if isinstance(parsed_data, list):
                skills_set.update(parsed_data)
                return skills_set
        except (ValueError, SyntaxError, TypeError): pass
        
        # Finally, assume comma-separated string (e.g., "Python, SQL, Git")
        skills_set.update([s.strip() for s in skill_data.split(',') if s.strip()])
    
    skills_set.discard('') # Remove any empty strings
    return skills_set

# --- 3. NEW Helper: Get StackOverflow Job Skill Set ---
def get_so_skill_set(so_job_dict):
    """
    Parses the multiple 'top_...' fields from a StackOverflow job dict.
    """
    skills_set = set()
    # Using the columns you specified:
    skill_columns = ['top_language', 'top_database', 'top_platform', 'top_framework']
    
    for col in skill_columns:
        skill_data = so_job_dict.get(col)
        if not skill_data:
            continue
        
        if isinstance(skill_data, list):
            skills_set.update(skill_data)
        elif isinstance(skill_data, str):
            # Clean string data like "['Python', 'Java']"
            cleaned_skill = skill_data.strip("[]'\" ")
            if not cleaned_skill:
                continue
            if ',' in cleaned_skill:
                 skills_set.update([s.strip(" '\"") for s in cleaned_skill.split(',')])
            else:
                skills_set.add(cleaned_skill)
    
    skills_set.discard('')
    return skills_set

# --- 4. NEW Helper: Compute Weight ---
# This is now a pure function that takes all values.
def compute_weight(salary_a, salary_b, exp_a, exp_b, skills_a, skills_b, norm_stats):
    """
    Compute weight of edge moving from job A (User) to job B (SO Job).
    Smaller weight = better transition.
    """
    # Use 0 as a default for missing data
    salary_a = salary_a or 0
    salary_b = salary_b or 0
    exp_a = exp_a or 0
    exp_b = exp_b or 0

    # --- Salary Component ---
    # Your algo: salary_diff = job_b - job_a.
    # Your comment: "higher salary in job B gives smaller weight"
    # These contradict. I will follow your comment's INTENT.
    # We'll calculate salary_component = job_a - job_b
    # This way, a salary INCREASE (job_b > job_a) results in a NEGATIVE number (good, smaller)
    salary_component = salary_a - salary_b
    
    # Normalize the component
    norm_salary_component = (salary_component - norm_stats['salary_comp_min']) / norm_stats['salary_comp_range']

    # --- Skill Component ---
    sim = jaccard_similarity(skills_a, skills_b)
    norm_skill_component = 1 - sim  # More overlap (high sim) = smaller weight (good)

    # --- Experience Component ---
    # Your algo: exp_diff = job_b - job_a. (lower increase = smaller weight)
    exp_component = exp_b - exp_a
    if exp_component < 0:
        exp_component = 0  # if job B requires less experience, set component to 0 (good)
    
    # Normalize the component
    norm_exp_component = (exp_component - norm_stats['exp_comp_min']) / norm_stats['exp_comp_range']

    # --- NEW: Define your weights ---
    # You can tune these numbers to get the results you want.
    # Higher number = more importance.
    
    weight_skill = 2.0   # <-- More emphasis on skills (2x)
    weight_salary = 0.5  # <-- Less emphasis on salary (0.5x)
    weight_exp = 1.0     # <-- Standard emphasis on experience

    # --- Final weight ---
    # Multiply each component by its assigned weight before summing
    return (weight_salary * norm_salary_component) + \
           (weight_skill * norm_skill_component) + \
           (weight_exp * norm_exp_component)

    # Final weight is the sum of normalized components
    return norm_salary_component + norm_skill_component + norm_exp_component

# --- 5. UPDATED graph_view Function ---

@login_required
def graph_view(request):
    """Renders the Skill Adjacency Graph page."""
    
    # --- 1. Get "Job A" (User's Profile) data ---
    
    # NEW: Get the logged-in auth user's ID (this is probably an integer)
    current_auth_user_id = request.user.id 
    print(f"Current Auth User ID: {current_auth_user_id}")

    try:
        # NEW: Use that ID to query your 'accounts_profile' (Users) table.
        # This assumes your 'Users' model has a field named 'user_id'
        # that stores the ID from the auth user.
        current_user_profile = AccountsProfile.objects.get(user_id=current_auth_user_id)
    
    except AccountsProfile.DoesNotExist:
        # Handle case where user is logged in but has no profile
        context = {
            'page_title': 'Skill Adjacency Graph',
            'active_nav_item': 'skillgraph',
            'error_message': "Your profile has not been set up. Please create your user profile to see recommendations.",
            'recommended_jobs': [],
            'graph_data': {'ego_node': 'Error', 'transitions': []},
        }
        return render(request, 'skillgraph/graph_view.html', context)
    
    # --- 2. Validate the profile data ---
    # (The rest of this function is now correct)
    if not all([current_user_profile.job_title, 
                current_user_profile.median_salary is not None, 
                current_user_profile.years_experience is not None]):
        
        context = {
            'page_title': 'Skill Adjacency Graph',
            'active_nav_item': 'skillgraph',
            'error_message': "Your profile is incomplete. Please set your job title, monthly salary, and years of experience to see recommendations.",
            'recommended_jobs': [],
            'graph_data': {'ego_node': 'Error', 'transitions': []},
        }
        return render(request, 'skillgraph/graph_view.html', context)
    
    # Get Job A's data from the profile
    job_a_salary = float(current_user_profile.median_salary * 12)
    job_a_exp = float(current_user_profile.years_experience)
    job_a_skills = get_user_skill_set(current_user_profile) 
    job_a_title = current_user_profile.job_title 

    # --- 3. Get ALL "Job B" data (StackOverflow) ---
    # (This section is unchanged)
    so_jobs_query = StackoverflowJobs2025.objects.values(
        'job', 
        'yearly_comp', 
        'work_exp', 
        'top_language', 
        'top_database', 
        'top_platform', 
        'top_framework'
    )
    
    # --- 4. Calculate Normalization Stats (Two-Pass Method) ---
    # (This section is unchanged)
    all_salary_comps = []
    all_exp_comps = []
    all_so_jobs_processed = []

    for job_b_raw in so_jobs_query:
        job_b_salary = job_b_raw.get('yearly_comp') or 0.0
        job_b_exp = job_b_raw.get('work_exp') or 0.0
        salary_comp = job_a_salary - job_b_salary
        all_salary_comps.append(salary_comp)
        exp_comp = job_b_exp - job_a_exp
        if exp_comp < 0:
            exp_comp = 0
        all_exp_comps.append(exp_comp)
        all_so_jobs_processed.append(job_b_raw)

    # (Rest of normalization stats logic is unchanged)
    norm_stats = {}
    norm_stats['salary_comp_min'] = min(all_salary_comps) if all_salary_comps else 0
    norm_stats['salary_comp_max'] = max(all_salary_comps) if all_salary_comps else 0
    norm_stats['salary_comp_range'] = (norm_stats['salary_comp_max'] - norm_stats['salary_comp_min']) or 1.0
    norm_stats['exp_comp_min'] = min(all_exp_comps) if all_exp_comps else 0
    norm_stats['exp_comp_max'] = max(all_exp_comps) if all_exp_comps else 0
    norm_stats['exp_comp_range'] = (norm_stats['exp_comp_max'] - norm_stats['exp_comp_min']) or 1.0


    # --- 5. Calculate Final Weights (Second Pass) ---
    # (This section is unchanged)
    graph_data = {
        'ego_node': f"My Role ({job_a_title})",
        'transitions': []
    }
    recommended_jobs = []

    for job_b_raw in all_so_jobs_processed:
        # ... (rest of loop) ...
        job_name_b = job_b_raw.get('job')
        job_b_salary = job_b_raw.get('yearly_comp')
        job_b_exp = job_b_raw.get('work_exp')
        job_b_skills = get_so_skill_set(job_b_raw)

        weight = compute_weight(
            job_a_salary, job_b_salary,
            job_a_exp, job_b_exp,
            job_a_skills, job_b_skills,
            norm_stats
        )

        graph_data['transitions'].append({
            'transition_job': job_name_b,
            'transition_weight': weight
        })
        
        recommended_jobs.append({
            'name': job_name_b,
            'skills': list(job_b_skills),
            'work_exp': job_b_exp,
            'yearly_comp': job_b_salary,
            'transition_weight': weight
        })
    
    # --- 6. SORT the list (unchanged) ---
    recommended_jobs.sort(key=lambda x: x['transition_weight'])

    # --- NEW: compute Top-3 easiest transitions on the spot (no persistence) ---
    # Get current user profile & skills
    profile = AccountsProfile.objects.filter(user_id=request.user.id).first()
    user_set = _user_skill_set_from_profile(profile) if profile else set()
    user_role = (getattr(profile, "job_title", None) or "Your Current Role") if profile else "Your Current Role"

    # Pull jobs (ORM hits Supabase because your default DB is SUPABASE_POOLER_URL)
    jobs_qs = StackoverflowJobs2025.objects.all()

    # Build lightweight edges (no graph drawing; just ranking)
    edges = []
    for job in jobs_qs:
        e = _edge_from_user_to_job(user_set, job, source_title=user_role)
        if e:
            edges.append(e)

    if user_role:
        edges = [e for e in edges if e["target"].casefold() != user_role.casefold()]

    # Sort easiest -> hardest: fewest missing, then more overlap, then title
    edges.sort(key=lambda e: (e["missing_count"], -e["overlap_count"], e["target"]))
    top3_edges = edges[:2]

    top_easiest_transitions = [
        {
            "title": e["target"],
            "ease": e["difficulty"],
            "missing_count": e["missing_count"],
            "overlap_count": e["overlap_count"],
            "missing": e["missing"],
            "overlap": e["overlap"],
        }
        for e in top3_edges
    ]

    # --- NEW: course recommendations per Top-2 job ---
    course_recommendations = []
    for e in top3_edges:
        job_title = e["target"]
        needed_skills = e["missing"]      # ONLY missing skills for matching
        overlap_skills = e["overlap"]     # skills the user already has
        recs = recommend_courses_for_job(job_title, needed_skills, exclude_skills=overlap_skills, k=10)

        course_recommendations.append({
            "job_title": job_title,
            "needed_skills": needed_skills,
            "courses": recs,
        })

    # include in context
    context = {
        'page_title': 'Skill Adjacency Graph',
        'intro_message': 'Visualize your career transitions.',
        'active_nav_item': 'skillgraph',
        'recommended_jobs': recommended_jobs,
        'graph_data': graph_data,
        'top_easiest_transitions': top_easiest_transitions,
        'course_recommendations': course_recommendations,  # <--- NEW
    }
    return render(request, 'skillgraph/graph_view.html', context)

# --- Embedding model cache (SentenceTransformer: all-MiniLM-L6-v2) ---
_ST_MODEL = None
def _get_st_model():
    global _ST_MODEL
    if _ST_MODEL is None:
        _ST_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _ST_MODEL

def _keyword_prefilter_q(needed_skills, exclude_skills=None):
    """Match ONLY missing skills; actively exclude overlap skills."""
    q = Q()
    for s in (needed_skills or [])[:12]:    # small cap to avoid huge WHERE
        s = (s or "").strip()
        if s:
            q |= Q(title__icontains=s) | Q(description__icontains=s)

    # negative clauses for overlap skills
    if exclude_skills:
        for s in exclude_skills:
            s = (s or "").strip()
            if s:
                q &= ~Q(title__icontains=s) & ~Q(description__icontains=s)
    return q


def _cos_sim(a, b):
    if a is None or b is None:
        return -1.0
    va = np.asarray(a, dtype=np.float32)
    vb = np.asarray(b, dtype=np.float32)
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return -1.0
    return float(np.dot(va/na, vb/nb))

def recommend_courses_for_job(job_title: str,
                              needed_skills: list[str],
                              exclude_skills: list[str] | None = None,
                              k: int = 10):
    # 1) pull candidate courses (no keyword filter; only global pool)
    qs = CoursesWithEmbeddings.objects.all()
    print(f"[DEBUG] Courses total pool: {qs.count()}")

    # limit the number of rows for performance if needed
    rows = list(qs.values("course_id", "title", "provider", "url", "description", "embeddings"))
    print(f"[DEBUG] Pulled {len(rows)} rows from Supabase")

    # 2) embed query text (job title + a few MISSING skills only)
    model = _get_st_model()
    query_text = job_title if not needed_skills else f"{job_title}: " + ", ".join(needed_skills[:8])
    qvec = model.encode(query_text).tolist()
    print(f"[DEBUG] Query text: {query_text}")
    
    # 3) cosine similarity between query and course embeddings
    usable, skipped, mismatched = 0, 0, 0
    for r in rows:
        emb = r.get("embeddings")
        if isinstance(emb, str):
            try:
                emb = json.loads(emb)
            except Exception:
                emb = None
        if not isinstance(emb, (list, tuple)):
            emb = None
        if emb and len(emb) == len(qvec):
            r["sim"] = _cos_sim(qvec, emb)
            usable += 1
        else:
            r["sim"] = -1.0
            if emb is None:
                skipped += 1
            else:
                mismatched += 1

    print(f"[DEBUG] Embedding stats — usable:{usable}, skipped:{skipped}, mismatched:{mismatched}")

    # 3b) remove any course that contains ANY overlap skill text (exclude_skills)
    if exclude_skills:
        excl = {s.lower() for s in exclude_skills if s}
        def has_overlap_text(r):
            hay = f"{r.get('title','')} {r.get('description','')}".lower()
            return any(s in hay for s in excl)
        rows = [r for r in rows if not has_overlap_text(r)]
        print(f"[DEBUG] After excluding overlap skills: {len(rows)} rows")

    # 3c) drop duplicate courses with identical title & description
    seen_pairs = set()
    unique_rows = []
    for r in rows:
        title = (r.get("title") or "").strip().lower()
        desc = (r.get("description") or "").strip().lower()
        pair = (title, desc)
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            unique_rows.append(r)
    print(f"[DEBUG] Deduped courses: {len(unique_rows)} (removed {len(rows) - len(unique_rows)})")

    rows = unique_rows

    # 4) compute lexical score and coverage score based on needed_skills
    needed_norm = [s.lower().strip() for s in (needed_skills or []) if s and s.strip()]
    n_needed = len(needed_norm)

    for r in rows:
        text = f"{r.get('title','')} {r.get('description','')}".lower()
        if n_needed > 0:
            hits = sum(1 for tok in needed_norm if tok in text)
            r["lex_raw"] = float(hits)                     # lexical: count of matched missing skills
            r["cov_raw"] = float(hits) / n_needed          # coverage: fraction of missing skills covered
        else:
            r["lex_raw"] = 0.0
            r["cov_raw"] = 0.0

    # 5) keep only rows with valid similarity and build arrays for normalization
    rows = [r for r in rows if r.get("sim", -1.0) >= 0]
    if not rows:
        print("[DEBUG] No rows with valid similarity")
        return []

    sims = np.array([r["sim"] for r in rows], dtype=np.float32)
    lex_raw = np.array([r["lex_raw"] for r in rows], dtype=np.float32)
    cov_raw = np.array([r["cov_raw"] for r in rows], dtype=np.float32)

    def _minmax(arr):
        if arr.size == 0:
            return arr
        a_min = float(arr.min())
        a_max = float(arr.max())
        if a_max <= a_min:
            return np.zeros_like(arr, dtype=np.float32)
        return (arr - a_min) / (a_max - a_min)

    sims_n = _minmax(sims)
    lex_n = _minmax(lex_raw)
    cov_n = _minmax(cov_raw)

    # 6) blended score: semantic + lexical + coverage
    w_sem = 0.6
    w_lex = 0.25
    w_cov = 0.15
    blended = w_sem * sims_n + w_lex * lex_n + w_cov * cov_n

    for i, r in enumerate(rows):
        r["score_sem"] = float(sims_n[i])
        r["score_lex"] = float(lex_n[i])
        r["score_cov"] = float(cov_n[i])
        r["score"] = float(blended[i])

    # 7) sort by blended score and return top-k
    rows.sort(
        key=lambda r: (
            -r["score"],          # main blended score
            -r["score_sem"],      # semantic tie-breaker
            -r["score_lex"],      # lexical tie-breaker
            -r["score_cov"],      # coverage tie-breaker
            r.get("title") or ""  # stable alphabetical fallback
        )
    )
    return rows[:k]
