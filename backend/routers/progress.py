"""
routers/progress.py — POST /progress-event
Logs learning events and triggers adaptive re-planning when needed.
"""

import json
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Learner, LearnerSkill, ProgressEvent, Resource, Skill
import path_engine
import schemas

router = APIRouter(prefix="/api", tags=["Progress"])

# XP rewards per event type
XP_REWARDS = {
    "started": 10,
    "completed": 100,
    "skipped": 5,
    "failed_checkpoint": 0,
}

# Badges (id, name, description, icon, condition_key)
BADGE_DEFINITIONS = [
    ("first_step",    "First Step",     "Completed your first resource",    "🎯", "completed_resources_1"),
    ("on_a_roll",     "On a Roll",      "Completed 5 resources",            "🔥", "completed_resources_5"),
    ("halfway_there", "Halfway There",  "Path is 50% complete",             "⚡", "path_50pct"),
    ("speed_learner", "Speed Learner",  "Completed 3 skills in one day",    "⚡", "three_in_a_day"),
    ("deep_diver",    "Deep Diver",     "Completed a difficulty-5 skill",   "🏆", "diff5_completed"),
    ("consistent",    "Consistent",     "3-day learning streak",            "📅", "streak_3"),
]


def _upsert_learner_skill(
    db: Session, learner_id: int, skill_id: int, status: str, delta_confidence: float = 0.0
):
    existing = (
        db.query(LearnerSkill)
        .filter(LearnerSkill.learner_id == learner_id, LearnerSkill.skill_id == skill_id)
        .first()
    )
    if existing:
        existing.status = status
        existing.confidence_score = min(1.0, max(0.0, (existing.confidence_score or 0.5) + delta_confidence))
    else:
        db.add(LearnerSkill(
            learner_id=learner_id,
            skill_id=skill_id,
            status=status,
            confidence_score=max(0.0, min(1.0, 0.5 + delta_confidence)),
        ))


def _update_streak(learner: Learner):
    today = date.today().isoformat()
    if learner.last_active_date == today:
        return  # Already counted today
    yesterday = (date.today().replace(day=date.today().day - 1)).isoformat()
    if learner.last_active_date == yesterday:
        learner.streak_days = (learner.streak_days or 0) + 1
    else:
        learner.streak_days = 1
    learner.last_active_date = today


@router.post("/progress-event", response_model=schemas.ProgressEventResponse)
def log_progress_event(request: schemas.ProgressEventRequest, db: Session = Depends(get_db)):
    """
    Log a learning event (started/completed/failed_checkpoint/skipped).
    Triggers re-planning when:
    - failed_checkpoint: reduces confidence, keeps skill in path, re-orders
    - skipped (already known): marks as completed, re-plans to prune redundant nodes
    """
    learner = db.query(Learner).filter(Learner.id == request.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Resolve skill_id from resource if not directly provided
    skill_id = request.skill_id
    resource = None
    if request.resource_id and not skill_id:
        resource = db.query(Resource).filter(Resource.id == request.resource_id).first()
        if resource:
            skill_id = resource.skill_id

    # Persist event
    event = ProgressEvent(
        learner_id=request.learner_id,
        resource_id=request.resource_id,
        skill_id=skill_id,
        event_type=request.event_type,
        timestamp=datetime.utcnow(),
        metadata_json=json.dumps(request.metadata or {}),
    )
    db.add(event)
    db.flush()

    # Update learner XP and streak
    xp_gain = XP_REWARDS.get(request.event_type, 0)
    learner.xp_points = (learner.xp_points or 0) + xp_gain
    _update_streak(learner)

    replanned = False
    updated_nodes = None
    message = f"Event '{request.event_type}' logged."

    # ── Adaptive re-planning logic ───────────────────────────────────────────
    if request.event_type == "failed_checkpoint" and skill_id:
        path_engine.insert_remedial_node(db, request.learner_id, skill_id)
        updated_nodes = path_engine.replan(db, request.learner_id)
        replanned = True
        message = (
            "Checkpoint failed. Your path has been adjusted to reinforce prerequisites "
            "before retrying this skill. You've got this! 💪"
        )

    elif request.event_type == "skipped" and skill_id:
        # Mark skill as completed (learner claims to already know it)
        _upsert_learner_skill(db, request.learner_id, skill_id, "completed", 0.3)
        db.flush()
        updated_nodes = path_engine.replan(db, request.learner_id)
        replanned = True
        xp_gain += 20  # bonus XP for skipping (showing prior knowledge)
        learner.xp_points = (learner.xp_points or 0) + 20
        message = (
            "Skill marked as already known! ✅ Your path has been pruned to remove "
            "now-redundant prerequisites downstream."
        )

    elif request.event_type == "completed" and skill_id:
        _upsert_learner_skill(db, request.learner_id, skill_id, "completed", 0.5)
        message = f"Skill completed! +{xp_gain} XP earned. 🎉"

    elif request.event_type == "started" and skill_id:
        _upsert_learner_skill(db, request.learner_id, skill_id, "in_progress", 0.0)
        message = f"Learning started! +{xp_gain} XP earned. Let's go! 🚀"

    db.commit()

    # Convert updated_nodes to PathNode schemas if present
    path_nodes = None
    if updated_nodes:
        path_nodes = [schemas.PathNode(**n) for n in updated_nodes]

    return schemas.ProgressEventResponse(
        event_id=event.id,
        replanned=replanned,
        message=message,
        updated_nodes=path_nodes,
    )
