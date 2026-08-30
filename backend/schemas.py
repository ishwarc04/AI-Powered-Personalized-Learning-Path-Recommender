"""
schemas.py — Pydantic v2 request / response models for PathMind API.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ---------------------------------------------------------------------------
# Learner / Onboarding
# ---------------------------------------------------------------------------

class OnboardRequest(BaseModel):
    name: str = Field(default="Learner")
    goal_text: str = Field(..., description="Free-text goal, e.g. 'become a data scientist in 6 months'")
    interests: List[str] = Field(default_factory=list)
    experience_level: str = Field(default="beginner")  # beginner | intermediate | advanced


class DiagnosticQuestion(BaseModel):
    question_id: str
    question_text: str
    skill_area: str
    options: Optional[List[str]] = None  # None = open-ended


class OnboardResponse(BaseModel):
    learner_id: int
    target_skills: List[str]
    diagnostic_questions: List[DiagnosticQuestion]
    message: str


class DiagnosticAnswer(BaseModel):
    question_id: str
    answer: str


class DiagnosticQuizRequest(BaseModel):
    learner_id: int
    answers: List[DiagnosticAnswer]


class SkillScore(BaseModel):
    skill_name: str
    confidence: float  # 0.0–1.0
    status: str  # unknown | in_progress | completed


class DiagnosticQuizResponse(BaseModel):
    learner_id: int
    skill_scores: List[SkillScore]
    message: str


# ---------------------------------------------------------------------------
# Learning Path
# ---------------------------------------------------------------------------

class GeneratePathRequest(BaseModel):
    learner_id: int


class PathNode(BaseModel):
    skill_id: int
    skill_name: str
    category: str
    description: str
    difficulty: int
    status: str  # locked | unlocked | in_progress | completed
    position: int  # order in path
    resources: List[ResourceOut] = Field(default_factory=list)
    is_milestone: bool = False
    prereq_skill_ids: List[int] = Field(default_factory=list)


class GeneratePathResponse(BaseModel):
    learner_id: int
    path_id: int
    nodes: List[PathNode]
    total_estimated_hours: float
    message: str


class PathResponse(BaseModel):
    learner_id: int
    path_id: Optional[int]
    nodes: List[PathNode]
    overall_progress: float  # 0.0–1.0
    total_estimated_hours: float


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

class ResourceOut(BaseModel):
    id: int
    title: str
    type: str
    difficulty: int
    url: str
    est_hours: float

    class Config:
        from_attributes = True


# Fix forward reference
PathNode.model_rebuild()


# ---------------------------------------------------------------------------
# Explain
# ---------------------------------------------------------------------------

class ExplainRequest(BaseModel):
    learner_id: int


class ExplainResponse(BaseModel):
    skill_id: int
    skill_name: str
    explanation: str
    cached: bool = False


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    learner_id: int
    message: str


class ChatResponse(BaseModel):
    learner_id: int
    reply: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Progress Events
# ---------------------------------------------------------------------------

class ProgressEventRequest(BaseModel):
    learner_id: int
    resource_id: Optional[int] = None
    skill_id: Optional[int] = None
    event_type: str  # started | completed | failed_checkpoint | skipped
    metadata: Optional[Dict[str, Any]] = None


class ProgressEventResponse(BaseModel):
    event_id: int
    replanned: bool
    message: str
    updated_nodes: Optional[List[PathNode]] = None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class CategoryStat(BaseModel):
    category: str
    total_skills: int
    completed_skills: int
    pct: float


class RecommendedAction(BaseModel):
    type: str  # start_resource | review_skill | take_quiz
    skill_name: str
    resource_title: Optional[str] = None
    resource_url: Optional[str] = None
    resource_type: Optional[str] = None
    reason: str


class Badge(BaseModel):
    name: str
    description: str
    icon: str
    earned_at: Optional[str] = None


class DashboardResponse(BaseModel):
    learner_id: int
    learner_name: str
    overall_progress: float
    completed_skills: int
    total_skills_in_path: int
    xp_points: int
    streak_days: int
    total_hours_spent: float
    category_stats: List[CategoryStat]
    recommended_actions: List[RecommendedAction]
    badges: List[Badge]
    weekly_plan: Optional[str] = None
