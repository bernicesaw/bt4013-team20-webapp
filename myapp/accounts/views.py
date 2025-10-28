import os
import json
import sys
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, authenticate
from django.contrib import messages

# ensure .env is loaded
try:
    from myapp import load_env  # loads .env into environment if present
except Exception:
    pass

from .forms import SignupForm, JOB_TITLE_CHOICES
from .models import Profile, WorkExperience

from supabase import create_client, Client


def get_supabase_client() -> Client:
    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_KEY', '')
    if not url or not key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY env vars not set")
    return create_client(url, key)


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            job_title = form.cleaned_data['job_title']
            skills = form.cleaned_data['skills']
            median_salary = form.cleaned_data['median_salary']
            currency = form.cleaned_data['currency']
            work_experiences = form.cleaned_data['work_experiences']

            # create Django user
            if User.objects.filter(username=email).exists():
                form.add_error('email', 'A user with that email already exists.')
            else:
                user = User.objects.create_user(username=email, email=email, password=password)
                profile = Profile.objects.create(
                    user=user,
                    job_title=job_title,
                    skills=skills,
                    median_salary=median_salary,
                    currency=currency
                )
                # create work experiences
                for idx, we in enumerate(work_experiences):
                    WorkExperience.objects.create(
                        profile=profile,
                        job_title=we.get('job_title', ''),
                        skills=we.get('skills', []),
                        median_salary=we.get('median_salary') or None,
                        currency=we.get('currency') or currency,
                        order=idx
                    )

                # Mirror to Supabase and print response for debugging
                try:
                    supabase = get_supabase_client()
                    # Prepare payload using native Python types for JSONB columns
                    payload = {
                        "email": email,
                        "job_title": job_title,
                        "skills": skills,
                        "median_salary": str(median_salary),
                        "currency": currency,
                        "work_experiences": work_experiences,
                    }

                    # Use upsert so repeated signups update existing record instead of failing
                    try:
                        resp = supabase.table('users').upsert(payload).execute()
                    except Exception as e:
                        # If upsert isn't supported or fails, fallback to insert and log the error
                        print('Supabase upsert failed, trying insert. Error:', e, file=sys.stderr)
                        try:
                            resp = supabase.table('users').insert(payload).execute()
                        except Exception as e2:
                            print('Supabase insert also failed:', e2, file=sys.stderr)
                            resp = None

                    # Print details to server console for debugging
                    if resp is not None:
                        try:
                            data = getattr(resp, 'data', None)
                            error = getattr(resp, 'error', None)
                            status = getattr(resp, 'status_code', None)
                            print("Supabase response - status:", status, file=sys.stderr)
                            print("Supabase response - data:", data, file=sys.stderr)
                            print("Supabase response - error:", error, file=sys.stderr)
                        except Exception:
                            try:
                                print("Supabase response (repr):", repr(resp), file=sys.stderr)
                            except Exception:
                                print("Supabase response: (unable to repr)", file=sys.stderr)
                except Exception as e:
                    # do not block signup on Supabase failure, but notify admin/log
                    print("Supabase insert failed:", e, file=sys.stderr)

                # log user in
                user = authenticate(request, username=email, password=password)
                if user:
                    auth_login(request, user)
                messages.success(request, "Account created and logged in.")
                return redirect('dashboard:dashboard_view')  # change redirect as appropriate
    else:
        form = SignupForm()
    # prepare job titles for client-side datalist (sorted alphabetically)
    # JOB_TITLE_CHOICES is a list of labels
    job_titles = sorted(JOB_TITLE_CHOICES)
    return render(request, 'accounts/signup.html', {'form': form, 'job_titles': job_titles})


from django.contrib.auth.views import LoginView

from django.contrib.auth import logout as auth_logout
from django.urls import reverse
from django.shortcuts import redirect


class SimpleLoginView(LoginView):
    template_name = 'accounts/login.html'


def logout_view(request):
    """Log out the current user and redirect to the login page.

    Accepts GET and POST so the Sign Out link can be a simple anchor.
    """
    try:
        auth_logout(request)
    except Exception:
        # ignore logout errors
        pass
    return redirect('accounts:login')