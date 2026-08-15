"""
Database connection setup.

Defaults to local SQLite (zero setup, file-based, free) so you can start
immediately. To use real PostgreSQL later (e.g. free tier on Neon/Supabase),
just set the DATABASE_URL environment variable — no code changes needed:

    postgresql://user:password@host:port/dbname

This is a standard pattern (12-factor app config) — same code works for
local dev and production, only the connection string changes.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./retail.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist yet."""
    from app import models  # noqa: F401 (ensures models are registered)
    Base.metadata.create_all(bind=engine)
