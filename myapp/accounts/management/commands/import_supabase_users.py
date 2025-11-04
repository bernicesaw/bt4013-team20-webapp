from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.views import get_supabase_client
from accounts.models import Profile, WorkExperience
import secrets


class Command(BaseCommand):
    help = 'Import users from Supabase "users" table into Django auth users (creates temporary passwords).'

    def handle(self, *args, **options):
        try:
            client = get_supabase_client(require_service_role=True)
        except Exception as e:
            self.stderr.write(f'Failed to create Supabase client: {e}')
            return

        try:
            resp = client.table('users').select('*').execute()
            data = getattr(resp, 'data', None)
        except Exception as e:
            self.stderr.write(f'Failed to query Supabase: {e}')
            return

        if not data:
            self.stdout.write('No users found in Supabase.')
            return

        created = 0
        for row in data:
            email = row.get('email')
            if not email:
                continue
            if User.objects.filter(username=email).exists():
                self.stdout.write(f'Skipping existing user: {email}')
                continue
            temp_pw = secrets.token_urlsafe(10)
            user = User.objects.create_user(username=email, email=email, password=temp_pw)
            # create or update profile
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.job_title = row.get('job_title') or ''
            profile.skills = row.get('skills') or []
            try:
                profile.median_salary = float(row.get('median_salary')) if row.get('median_salary') is not None else None
            except Exception:
                profile.median_salary = None
            profile.currency = row.get('currency') or ''
            profile.years_experience = row.get('years_experience') or None
            profile.notifications_enabled = bool(row.get('notifications_enabled'))
            profile.save()
            # optional: ignore work_experiences or create entries
            created += 1
            self.stdout.write(f'Created user {email} with temporary password: {temp_pw}')

        self.stdout.write(f'Import complete. Created {created} users.')
