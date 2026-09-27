from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL


def _normalize_url(url):
    # Neon and most hosts hand out "postgresql://..." URLs. SQLAlchemy would pick
    # the old psycopg2 driver for that, so we point it at psycopg (v3) instead.
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(_normalize_url(DATABASE_URL), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    # create_all only creates tables that don't exist yet. It won't change
    # existing tables. For schema changes you'd use a migration tool like Alembic.
    from database import models  # noqa: F401  (registers the tables on Base)

    Base.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: one session per request, always closed afterwards."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
