from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Use DATABASE_URL environment variable (e.g. for RDS). Fall back to sqlite for local dev.
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./messenger.db')

# If using sqlite, set check_same_thread; for other DBs this arg should not be provided.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Yield a SQLAlchemy DB session for use as a dependency.

    The function returns a generator suitable for FastAPI's "Depends".
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
