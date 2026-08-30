"""
routers/chat.py — POST /chat
AI tutor chat with learner profile + path context injected into every call.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Learner, LearningPath, ChatHistory
import ai_client
import schemas

router = APIRouter(prefix="/api", tags=["Chat"])


def _build_path_summary(lp) -> str:
    """Summarise the learning path as a short text for the LLM system prompt."""
    if not lp:
        return "No learning path generated yet."

    nodes = lp.path_json
    completed = [n for n in nodes if n["status"] == "completed"]
    in_progress = [n for n in nodes if n["status"] == "in_progress"]
    unlocked = [n for n in nodes if n["status"] == "unlocked"]

    summary_parts = [
        f"Total skills in path: {len(nodes)}",
        f"Completed: {', '.join(n['skill_name'] for n in completed) or 'none'}",
        f"In progress: {', '.join(n['skill_name'] for n in in_progress) or 'none'}",
        f"Next up (unlocked): {', '.join(n['skill_name'] for n in unlocked[:3]) or 'none'}",
    ]
    return " | ".join(summary_parts)


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    AI tutor chat. Has full access to learner profile + current path context.
    Saves every exchange to chat_history.
    """
    learner = db.query(Learner).filter(Learner.id == request.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Fetch active path
    lp = (
        db.query(LearningPath)
        .filter(LearningPath.learner_id == request.learner_id, LearningPath.status == "active")
        .order_by(LearningPath.generated_at.desc())
        .first()
    )

    path_summary = _build_path_summary(lp)

    # Fetch recent chat history
    history = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.learner_id == request.learner_id,
            ChatHistory.role.in_(["user", "assistant"]),
        )
        .order_by(ChatHistory.timestamp.asc())
        .limit(20)
        .all()
    )
    history_dicts = [{"role": h.role, "message": h.message} for h in history]

    # Save user message
    db.add(ChatHistory(
        learner_id=request.learner_id,
        role="user",
        message=request.message,
    ))
    db.flush()

    try:
        reply = ai_client.chat_response(
            learner_name=learner.name,
            learner_goal=learner.goals_text,
            experience_level=learner.experience_level,
            current_path_summary=path_summary,
            chat_history=history_dicts,
            new_message=request.message,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    # Save assistant reply
    db.add(ChatHistory(
        learner_id=request.learner_id,
        role="assistant",
        message=reply,
    ))
    db.commit()

    return schemas.ChatResponse(
        learner_id=request.learner_id,
        reply=reply,
        timestamp=datetime.utcnow(),
    )
