# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AccountsProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    job_title = models.CharField(max_length=200)
    skills = models.JSONField()
    median_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=32)
    user = models.OneToOneField('AuthUser', models.DO_NOTHING)
    notifications_enabled = models.BooleanField()
    years_experience = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'accounts_profile'


class AccountsWorkexperience(models.Model):
    id = models.BigAutoField(primary_key=True)
    job_title = models.CharField(max_length=200)
    skills = models.JSONField()
    median_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=32)
    order = models.SmallIntegerField()
    profile = models.ForeignKey(AccountsProfile, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'accounts_workexperience'


class AllCourses(models.Model):
    source = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    level = models.TextField(blank=True, null=True)
    duration = models.TextField(blank=True, null=True)
    description_full = models.TextField(blank=True, null=True)
    url = models.TextField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'all_courses'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class ChatbotChathistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    session_id = models.CharField(max_length=100)
    query = models.TextField()
    response = models.TextField()
    tool_used = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField()
    response_time = models.FloatField(blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'chatbot_chathistory'


class CodecademyRaw(models.Model):
    title = models.TextField(blank=True, null=True)
    level = models.TextField(blank=True, null=True)
    duration = models.TextField(blank=True, null=True)
    description_full = models.TextField(blank=True, null=True)
    url = models.TextField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'codecademy_raw'


class CourseraRaw(models.Model):
    keyword = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    partner = models.TextField(blank=True, null=True)
    level = models.TextField(blank=True, null=True)
    rating = models.TextField(blank=True, null=True)
    rating_count = models.TextField(blank=True, null=True)
    duration = models.TextField(blank=True, null=True)
    what_you_will_learn = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    recommended_experience = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url = models.TextField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'coursera_raw'


class DatacampRaw(models.Model):
    title = models.TextField(blank=True, null=True)
    level = models.TextField(blank=True, null=True)
    duration = models.TextField(blank=True, null=True)
    description_full = models.TextField(blank=True, null=True)
    url = models.TextField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'datacamp_raw'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class LangchainPgCollection(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(unique=True)
    cmetadata = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'langchain_pg_collection'


class LangchainPgEmbedding(models.Model):
    id = models.CharField(primary_key=True)
    collection = models.ForeignKey(LangchainPgCollection, models.DO_NOTHING, blank=True, null=True)
    embedding = models.TextField(blank=True, null=True)  # This field type is a guess.
    document = models.CharField(blank=True, null=True)
    cmetadata = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'langchain_pg_embedding'


class StackoverflowDataCleaned2025(models.Model):
    response_id = models.BigIntegerField(primary_key=True)
    ed_level = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    role = models.TextField(blank=True, null=True)
    work_exp = models.TextField(blank=True, null=True)
    comp = models.TextField(blank=True, null=True)
    language_have = models.TextField(blank=True, null=True)
    language_want = models.TextField(blank=True, null=True)
    database_have = models.TextField(blank=True, null=True)
    database_want = models.TextField(blank=True, null=True)
    platform_have = models.TextField(blank=True, null=True)
    platform_want = models.TextField(blank=True, null=True)
    webframe_have = models.TextField(blank=True, null=True)
    webframe_want = models.TextField(blank=True, null=True)
    devenvs_have = models.TextField(blank=True, null=True)
    devenvs_want = models.TextField(blank=True, null=True)
    job_sat = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stackoverflow_data_cleaned_2025'
        db_table_comment = 'newest version'


class StackoverflowDataCleanedMultiYear(models.Model):
    response_id = models.BigIntegerField(primary_key=True)
    year = models.BigIntegerField(blank=True, null=True)
    ed_level = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    role = models.TextField(blank=True, null=True)
    work_exp = models.TextField(blank=True, null=True)
    comp = models.TextField(blank=True, null=True)
    language_have = models.TextField(blank=True, null=True)
    language_want = models.TextField(blank=True, null=True)
    database_have = models.TextField(blank=True, null=True)
    database_want = models.TextField(blank=True, null=True)
    platform_have = models.TextField(blank=True, null=True)
    platform_want = models.TextField(blank=True, null=True)
    webframe_have = models.TextField(blank=True, null=True)
    webframe_want = models.TextField(blank=True, null=True)
    job_sat = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stackoverflow_data_cleaned_multi_year'


class StackoverflowDataCleanedMultiYearExploded(models.Model):
    response_id = models.BigIntegerField(blank=True, null=True)
    year = models.BigIntegerField(blank=True, null=True)
    ed_level = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    role = models.TextField(blank=True, null=True)
    work_exp = models.TextField(blank=True, null=True)
    comp = models.TextField(blank=True, null=True)
    language_have = models.TextField(blank=True, null=True)
    language_want = models.TextField(blank=True, null=True)
    database_have = models.TextField(blank=True, null=True)
    database_want = models.TextField(blank=True, null=True)
    platform_have = models.TextField(blank=True, null=True)
    platform_want = models.TextField(blank=True, null=True)
    webframe_have = models.TextField(blank=True, null=True)
    webframe_want = models.TextField(blank=True, null=True)
    job_sat = models.TextField(blank=True, null=True)
    id = models.BigAutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'stackoverflow_data_cleaned_multi_year_exploded'


class StackoverflowJobs2025(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    job = models.TextField(blank=True, null=True)
    top_language = models.JSONField(blank=True, null=True)
    top_database = models.JSONField(blank=True, null=True)
    top_platform = models.JSONField(blank=True, null=True)
    top_framework = models.JSONField(blank=True, null=True)
    work_exp = models.FloatField(blank=True, null=True)
    yearly_comp = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stackoverflow_jobs_2025'


class Users(models.Model):
    id = models.UUIDField(primary_key=True)
    email = models.TextField(unique=True)
    job_title = models.TextField(blank=True, null=True)
    skills = models.JSONField(blank=True, null=True)
    median_salary = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    currency = models.TextField(blank=True, null=True)
    work_experiences = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    notifications_enabled = models.BooleanField(blank=True, null=True)
    job_transitions = models.JSONField(blank=True, null=True)
    years_experience = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
