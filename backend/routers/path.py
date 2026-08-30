"""
routers/path.py — POST /generate-path and GET /path/{learner_id}
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Learner, LearningPath, LearnerSkill, Skill
import path_engine
import schemas

router = APIRouter(prefix="/api", tags=["Learning Path"])


def _resolve_target_skill_ids(db: Session, target_names: List[str]) -> set:
    """Match skill names (from LLM) to DB skill IDs — case-insensitive."""
    skills = db.query(Skill).all()
    name_to_id = {s.name.lower(): s.id for s in skills}
    ids = set()
    for name in target_names:
        sid = name_to_id.get(name.lower())
        if sid:
            ids.add(sid)
    return ids


def _get_learner_skill_map(db: Session, learner_id: int) -> dict:
    rows = db.query(LearnerSkill).filter(LearnerSkill.learner_id == learner_id).all()
    return {row.skill_id: row.status for row in rows}


@router.post("/generate-path", response_model=schemas.GeneratePathResponse)
def generate_path(request: schemas.GeneratePathRequest, db: Session = Depends(get_db)):
    """
    Run the networkx graph algorithm to compute the minimal learning path
    from current known skills to target skills. Stores the result in learning_paths.
    """
    learner = db.query(Learner).filter(Learner.id == request.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Retrieve stored target skills from chat history (set during onboarding)
    # Look for the most recent onboard system message
    from models import ChatHistory
    system_msg = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.learner_id == request.learner_id,
            ChatHistory.role == "system",
        )
        .order_by(ChatHistory.timestamp.desc())
        .first()
    )

    # Parse target skills from the system message or fall back to all advanced skills
    target_names: List[str] = []
    if system_msg and "target_skills=" in system_msg.message:
        import ast
        try:
            ts_str = system_msg.message.split("target_skills=")[1]
            target_names = ast.literal_eval(ts_str)
        except Exception:
            pass

    # If no target skills found, default to the full DS path
    if not target_names:
        target_names = ["End-to-End DS Project", "Model Deployment", "Deep Learning Basics"]

    target_ids = _resolve_target_skill_ids(db, target_names)
    if not target_ids:
        # Fall back: use the top-level skills
        top_skills = db.query(Skill).filter(Skill.difficulty >= 4).all()
        target_ids = {s.id for s in top_skills}

    G = path_engine.build_graph(db)
    known_ids = path_engine.get_learner_known_skills(db, learner.id)
    ordered_ids = path_engine.compute_path(db, G, known_ids, target_ids)

    learner_skill_map = _get_learner_skill_map(db, learner.id)
    nodes = path_engine.build_path_nodes(db, G, ordered_ids, known_ids, learner_skill_map)

    # Deactivate any previous active paths
    db.query(LearningPath).filter(
        LearningPath.learner_id == learner.id,
        LearningPath.status == "active",
    ).update({"status": "abandoned"})

    # Create new path record
    lp = LearningPath(
        learner_id=learner.id,
        generated_at=datetime.utcnow(),
        status="active",
    )
    lp.path_json = nodes
    lp.target_skills = target_names
    db.add(lp)
    db.commit()
    db.refresh(lp)

    total_hours = sum(
        r["est_hours"]
        for n in nodes
        for r in n.get("resources", [])
    )

    return schemas.GeneratePathResponse(
        learner_id=learner.id,
        path_id=lp.id,
        nodes=[schemas.PathNode(**n) for n in nodes],
        total_estimated_hours=round(total_hours, 1),
        message=(
            f"Your personalised path is ready! {len(nodes)} skills to master, "
            f"estimated {round(total_hours, 0):.0f} hours of learning."
        ),
    )


@router.get("/path/{learner_id}", response_model=schemas.PathResponse)
def get_path(learner_id: int, db: Session = Depends(get_db)):
    """Return the current active learning path with live status for each node."""
    learner = db.query(Learner).filter(Learner.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    lp = (
        db.query(LearningPath)
        .filter(LearningPath.learner_id == learner_id, LearningPath.status == "active")
        .order_by(LearningPath.generated_at.desc())
        .first()
    )

    if not lp:
        raise HTTPException(
            status_code=404,
            detail="No active learning path found. Please call /generate-path first.",
        )

    # Refresh node statuses based on current learner_skills
    G = path_engine.build_graph(db)
    known_ids = path_engine.get_learner_known_skills(db, learner_id)
    learner_skill_map = _get_learner_skill_map(db, learner_id)

    # Get ordered skill ids from stored path
    raw_nodes = lp.path_json
    ordered_ids = [n["skill_id"] for n in raw_nodes]

    fresh_nodes = path_engine.build_path_nodes(db, G, ordered_ids, known_ids, learner_skill_map)

    total_hours = sum(r["est_hours"] for n in fresh_nodes for r in n.get("resources", []))
    completed = sum(1 for n in fresh_nodes if n["status"] == "completed")
    progress = completed / len(fresh_nodes) if fresh_nodes else 0.0

    return schemas.PathResponse(
        learner_id=learner_id,
        path_id=lp.id,
        nodes=[schemas.PathNode(**n) for n in fresh_nodes],
        overall_progress=round(progress, 3),
        total_estimated_hours=round(total_hours, 1),
    )
