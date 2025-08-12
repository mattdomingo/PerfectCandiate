import os
from sqlalchemy import create_engine, text

def get_engine():
    dsn = (
        f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(dsn, pool_pre_ping=True)

def init_db(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            create table if not exists health_probe(
                id serial primary key,
                created_at timestamptz default now()
            )
        """))
        conn.execute(text("""
            create table if not exists resumes (
                id uuid primary key,
                user_id uuid,
                s3_key text not null,
                json_resume jsonb,
                created_at timestamptz default now()
            )
        """))
        conn.execute(text("""
            create table if not exists job_posts (
                id uuid primary key,
                user_id uuid,
                source_url text,
                text_content text not null,
                extracted jsonb,
                created_at timestamptz default now()
            )
        """))
        conn.execute(text("""
            create table if not exists resume_versions (
                id uuid primary key,
                resume_id uuid references resumes(id),
                json_resume jsonb not null,
                created_at timestamptz default now()
            )
        """))


