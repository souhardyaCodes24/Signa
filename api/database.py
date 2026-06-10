"""
database.py — manages the SQLAlchemy engine and session.

For local dev we use SQLite (no server needed).
When you're ready for cloud, swap DATABASE_URL to the Neon
PostgreSQL connection string and uncomment the psycopg2 driver.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv

# Load variables from .env (if it exists)
load_dotenv()

# ── Database URL ──
# Default: SQLite file stored in the project root
# Override via env var when deploying:  SIGN_DB_URL=postgresql://...
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)

SQLITE_URL = f"sqlite:///{DB_DIR / 'signa.db'}"
DATABASE_URL = os.getenv("SIGN_DB_URL", SQLITE_URL)

# ── Engine ──
# connect_args needed for SQLite to allow concurrent access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,   # set True to see every SQL query in the console
)

# ── Session factory ──
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    """
    FastAPI dependency — provides a database session and
    automatically closes it when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
