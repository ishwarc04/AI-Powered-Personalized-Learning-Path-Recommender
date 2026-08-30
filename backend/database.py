"""
database.py — SQLAlchemy engine, session factory, and DB initialization.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'pathmind.db')}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and seed data if the DB is empty."""
    # Import models so Base knows about them before create_all
    from models import (  # noqa: F401
        Learner, Skill, SkillPrereq, Resource,
        LearnerSkill, LearningPath, ProgressEvent, ChatHistory,
    )
    Base.metadata.create_all(bind=engine)

    # Seed only when skills table is empty
    db = SessionLocal()
    try:
        from models import Skill as SkillModel
        if db.query(SkillModel).count() == 0:
            from seed_data import seed
            seed(db)
    finally:
        db.close()
