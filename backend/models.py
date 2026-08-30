"""
models.py — SQLAlchemy ORM models for PathMind.
"""

import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database import Base


class Learner(Base):
    __tablename__ = "learners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, default="Learner")
    experience_level = Column(String(50), default="beginner")  # beginner | intermediate | advanced
    _interests = Column("interests", Text, default="[]")
    goals_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # XP / gamification
    xp_points = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_active_date = Column(String(20), nullable=True)

    # Relationships
    skills = relationship("LearnerSkill", back_populates="learner", cascade="all, delete-orphan")
    paths = relationship("LearningPath", back_populates="learner", cascade="all, delete-orphan")
    events = relationship("ProgressEvent", back_populates="learner", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="learner", cascade="all, delete-orphan")

    @property
    def interests(self):
        return json.loads(self._interests or "[]")

    @interests.setter
    def interests(self, value):
        self._interests = json.dumps(value)


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    category = Column(String(100), nullable=False)  # e.g. Programming, Statistics, ML, etc.
    description = Column(Text, default="")
    difficulty = Column(Integer, default=1)  # 1–5

    # Relationships
    resources = relationship("Resource", back_populates="skill", cascade="all, delete-orphan")
    prereq_links = relationship(
        "SkillPrereq", foreign_keys="SkillPrereq.skill_id",
        back_populates="skill", cascade="all, delete-orphan",
    )
    dependent_links = relationship(
        "SkillPrereq", foreign_keys="SkillPrereq.prereq_skill_id",
        back_populates="prereq_skill",
    )
    learner_skills = relationship("LearnerSkill", back_populates="skill")


class SkillPrereq(Base):
    """Edge in the prerequisite DAG: skill_id requires prereq_skill_id."""
    __tablename__ = "skill_prereqs"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    prereq_skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)

    __table_args__ = (UniqueConstraint("skill_id", "prereq_skill_id"),)

    skill = relationship("Skill", foreign_keys=[skill_id], back_populates="prereq_links")
    prereq_skill = relationship("Skill", foreign_keys=[prereq_skill_id], back_populates="dependent_links")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    type = Column(String(50), nullable=False)  # course | project | article | video | quiz
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    difficulty = Column(Integer, default=1)  # 1–5
    url = Column(Text, default="")
    est_hours = Column(Float, default=1.0)

    skill = relationship("Skill", back_populates="resources")


class LearnerSkill(Base):
    __tablename__ = "learner_skills"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    status = Column(String(50), default="unknown")  # unknown | in_progress | completed
    confidence_score = Column(Float, default=0.0)  # 0.0–1.0

    __table_args__ = (UniqueConstraint("learner_id", "skill_id"),)

    learner = relationship("Learner", back_populates="skills")
    skill = relationship("Skill", back_populates="learner_skills")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    _path_json = Column("path_json", Text, default="[]")
    status = Column(String(50), default="active")  # active | completed | abandoned
    target_skills_json = Column(Text, default="[]")

    learner = relationship("Learner", back_populates="paths")

    @property
    def path_json(self):
        return json.loads(self._path_json or "[]")

    @path_json.setter
    def path_json(self, value):
        self._path_json = json.dumps(value)

    @property
    def target_skills(self):
        return json.loads(self.target_skills_json or "[]")

    @target_skills.setter
    def target_skills(self, value):
        self.target_skills_json = json.dumps(value)


class ProgressEvent(Base):
    __tablename__ = "progress_events"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # started | completed | failed_checkpoint | skipped
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, default="{}")

    learner = relationship("Learner", back_populates="events")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant | system
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner", back_populates="chat_history")


class SkillExplanationCache(Base):
    """Cache for LLM-generated skill explanations to avoid repeated API calls."""
    __tablename__ = "skill_explanation_cache"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("learner_id", "skill_id"),)
