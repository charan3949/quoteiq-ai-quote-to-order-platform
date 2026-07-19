from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def _normalize_database_url(raw_url: str) -> str:
    # Render (and Heroku-style providers) hand out URLs prefixed
    # "postgres://", but SQLAlchemy 1.4+/2.0 requires "postgresql://"
    # for the driver dialect lookup to succeed.
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql://", 1)

    return raw_url


DATABASE_URL = _normalize_database_url(settings.database_url)

engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False}
        if DATABASE_URL.startswith("sqlite")
        else {}
    ),
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():
    database = SessionLocal()

    try:
        yield database
    finally:
        database.close()