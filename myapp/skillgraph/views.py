import json
import ast
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import StackoverflowJobs2025, AccountsProfile  # Assuming Users is your accounts_profile model
from django.db.models import Min, Max

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
    
    # --- 6. SORT the list ---
    # (This section is unchanged)
    recommended_jobs.sort(key=lambda x: x['transition_weight'])

    # --- 7. Set up context ---
    # (This section is unchanged)
    context = {
        'page_title': 'Skill Adjacency Graph',
        'intro_message': 'Visualize your career transitions.',
        'active_nav_item': 'skillgraph', 
        'recommended_jobs': recommended_jobs,
        'graph_data': graph_data,
    }
    return render(request, 'skillgraph/graph_view.html', context)