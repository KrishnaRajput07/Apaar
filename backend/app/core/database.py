from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
from .config import settings


# Sync engine (psycopg3 sync driver)
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Create tables that don't exist yet (used in dev/test)."""
    Base.metadata.create_all(bind=engine)


def run_sql_file(path: str):
    """Execute a raw SQL file (used for extensions and functions)."""
    with open(path) as f:
        sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(sql))
