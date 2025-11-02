# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


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


class SurveyResultsPublic2025(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'survey_results_public_2025'


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

    class Meta:
        managed = False
        db_table = 'users'
