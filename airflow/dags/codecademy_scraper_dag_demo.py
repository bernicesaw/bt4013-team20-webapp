# airflow/dags/codecademy_scraper_dag_demo.py
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import os

# Use the *codecademy* DB helper (targets public.codecademy_demo with same schema)
from scripts.db_supabase_codecademy import ensure_table_exists, upsert_rows

# Reuse the Coursera scraper + transform so the DAG can run successfully
from scripts.coursera_scraper import scrape_coursera_rows_sync, transform_for_db

def _create_table():
    # make sure the Supabase URL is present (injected via docker-compose env_file)
    if not os.getenv("SUPABASE_POOLER_URL") and not os.getenv("SUPABASE_DB_URL"):
        raise RuntimeError("Missing SUPABASE_POOLER_URL or SUPABASE_DB_URL in environment")
    ensure_table_exists()  # creates public.codecademy_demo (identical schema to coursera_demo)
    print("✅ ensured public.codecademy_demo exists")

def _scrape_and_upsert():
    # Behind the scenes we scrape Coursera but save into codecademy_demo
    rows = scrape_coursera_rows_sync(
        keywords_csv="python, data science",  # tweak as you like
        pages=2,
        concurrency=8,
    )
    print(f"✅ scraped {len(rows)} (from Coursera; codecademy demo)")
    formatted = transform_for_db(rows)  # already matches our table schema
    total = upsert_rows(formatted)      # writes to public.codecademy_demo
    print(f"✅ upserted {total} rows into public.codecademy_demo")

with DAG(
    dag_id="codecademy_scraper_dag_demo",
    start_date=datetime(2024, 1, 1),
    schedule=None,         # manual run
    catchup=False,
    tags=["demo", "supabase", "codecademy"],
) as dag:

    create_table = PythonOperator(
        task_id="create_table_if_needed",
        python_callable=_create_table,
    )

    scrape_and_upsert = PythonOperator(
        task_id="scrape_and_upsert_to_supabase",
        python_callable=_scrape_and_upsert,
    )

    create_table >> scrape_and_upsert
