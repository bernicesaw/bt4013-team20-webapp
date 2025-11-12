# scripts/db_supabase_codecademy.py
from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List
from sqlalchemy import create_engine, text

# Write to this table (same level as datacamp_raw)
TABLE_FQN = "public.codecademy_demo"

def _resolve_db_url() -> str:
    """
    Accept both:
      - SUPABASE_DB_URL (SQLAlchemy form)
      - SUPABASE_POOLER_URL (webapp form)
    Force psycopg2 and sslmode=require.
    """
    url = os.getenv("SUPABASE_DB_URL") or os.getenv("SUPABASE_POOLER_URL")
    if not url:
        raise RuntimeError("Missing DB URL. Set SUPABASE_DB_URL or SUPABASE_POOLER_URL")

    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url

def _get_engine():
    url = _resolve_db_url()
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})

DDL_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_FQN} (
    course_id TEXT PRIMARY KEY,
    title TEXT,
    provider TEXT,
    url TEXT,
    price TEXT,
    duration TEXT,
    level TEXT,
    language TEXT,
    rating NUMERIC,
    reviews_count INTEGER,
    last_updated DATE,
    keyword TEXT,
    description TEXT,
    what_you_will_learn TEXT,
    skills TEXT,
    recommended_experience TEXT
);
"""

def ensure_table_exists() -> None:
    eng = _get_engine()
    with eng.begin() as conn:
        conn.execute(text("SELECT 1"))
        conn.execute(text(DDL_SQL))

_COLUMNS: List[str] = [
    "course_id","title","provider","url","price","duration","level","language",
    "rating","reviews_count","last_updated","keyword","description",
    "what_you_will_learn","skills","recommended_experience",
]

_INSERT_SQL = f"""
INSERT INTO {TABLE_FQN} ({", ".join(_COLUMNS)})
VALUES ({", ".join(f":{c}" for c in _COLUMNS)})
ON CONFLICT (course_id) DO UPDATE SET
{", ".join(f"{c}=EXCLUDED.{c}" for c in _COLUMNS if c != "course_id")};
"""

def _coerce_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {c: row.get(c) for c in _COLUMNS}

def upsert_rows(rows: Iterable[Dict[str, Any]], chunk_size: int = 1000) -> int:
    eng = _get_engine()
    total = 0
    batch: List[Dict[str, Any]] = []
    with eng.begin() as conn:
        for r in rows:
            batch.append(_coerce_row(r))
            if len(batch) >= chunk_size:
                conn.execute(text(_INSERT_SQL), batch)
                total += len(batch)
                batch = []
        if batch:
            conn.execute(text(_INSERT_SQL), batch)
            total += len(batch)
    return total
