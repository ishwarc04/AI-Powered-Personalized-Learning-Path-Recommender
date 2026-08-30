"""
routers/onboard.py — POST /onboard and POST /diagnostic-quiz
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Learner, LearnerSkill, Skill, ChatHistory
import ai_client
import schemas

router = APIRouter(prefix="/api", tags=["Onboarding"])

# In-memory store for diagnostic questions during a session
# (small prototype: no persistent quiz session table needed)
_quiz_store: dict = {}  # learner_id -> list of DiagnosticQuestion dicts


@router.post("/onboard", response_model=schemas.OnboardResponse)
def onboard(request: schemas.OnboardRequest, db: Session = Depends(get_db)):
    """
    Accept learner's free-text goal + interests + experience level.
    Calls Grok to extract target skills and generate diagnostic quiz questions.
    Creates a new Learner record and returns quiz questions.
    """
    # Create learner record
    learner = Learner(
        name=request.name,
        experience_level=request.experience_level,
        goals_text=request.goal_text,
    )
    learner.interests = request.interests
    db.add(learner)
    db.flush()  # Get learner.id

    # Fetch available skills to ground the LLM
    skills = db.query(Skill).all()
    available_skills = [{"name": s.name, "category": s.category} for s in skills]

    # Call Grok
    try:
        result = ai_client.extract_goals(
            goal_text=request.goal_text,
            interests=request.interests,
            experience_level=request.experience_level,
            available_skills=available_skills,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    target_skills = result.get("target_skills", [])
    raw_questions = result.get("diagnostic_questions", [])

    # Normalise questions
    questions = []
    for q in raw_questions:
        questions.append(
            schemas.DiagnosticQuestion(
                question_id=q.get("question_id", f"q{len(questions)+1}"),
                question_text=q.get("question_text", ""),
                skill_area=q.get("skill_area", ""),
                options=q.get("options"),
            )
        )

    # Store questions for later quiz scoring
    _quiz_store[learner.id] = [q.model_dump() for q in questions]

    # Store initial system message in chat history
    db.add(ChatHistory(
        learner_id=learner.id,
        role="system",
        message=(
            f"Learner profile: name={request.name}, "
            f"goal={request.goal_text}, "
            f"experience={request.experience_level}, "
            f"target_skills={target_skills}"
        ),
    ))

    db.commit()

    return schemas.OnboardResponse(
        learner_id=learner.id,
        target_skills=target_skills,
        diagnostic_questions=questions,
        message=(
            f"Welcome {request.name}! I've analysed your goal and prepared "
            f"{len(questions)} diagnostic questions to personalise your path."
        ),
    )


@router.post("/diagnostic-quiz", response_model=schemas.DiagnosticQuizResponse)
def diagnostic_quiz(request: schemas.DiagnosticQuizRequest, db: Session = Depends(get_db)):
    """
    Accept quiz answers, call Grok to score them, update learner_skills table.
    """
    learner = db.query(Learner).filter(Learner.id == request.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    questions = _quiz_store.get(request.learner_id, [])
    if not questions:
        raise HTTPException(status_code=400, detail="No active quiz found for this learner. Please call /onboard first.")

    skills = db.query(Skill).all()
    available_skills = [{"name": s.name} for s in skills]

    try:
        scoring = ai_client.score_quiz(
            questions=questions,
            answers=[a.model_dump() for a in request.answers],
            available_skills=available_skills,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    skill_scores = scoring.get("skill_scores", [])

    # Build name→id map
    name_to_id = {s.name: s.id for s in skills}

    updated_scores = []
    for score in skill_scores:
        skill_name = score.get("skill_name", "")
        confidence = float(score.get("confidence", 0.0))
        status = score.get("status", "unknown")

        skill_id = name_to_id.get(skill_name)
        if not skill_id:
            # Try case-insensitive match
            for s in skills:
                if s.name.lower() == skill_name.lower():
                    skill_id = s.id
                    break

        if skill_id:
            existing = (
                db.query(LearnerSkill)
                .filter(
                    LearnerSkill.learner_id == request.learner_id,
                    LearnerSkill.skill_id == skill_id,
                )
                .first()
            )
            if existing:
                existing.confidence_score = confidence
                existing.status = status
            else:
                db.add(LearnerSkill(
                    learner_id=request.learner_id,
                    skill_id=skill_id,
                    status=status,
                    confidence_score=confidence,
                ))

            updated_scores.append(
                schemas.SkillScore(
                    skill_name=skill_name,
                    confidence=confidence,
                    status=status,
                )
            )

    # Clean up quiz store
    _quiz_store.pop(request.learner_id, None)
    db.commit()

    completed_count = sum(1 for s in updated_scores if s.status == "completed")
    return schemas.DiagnosticQuizResponse(
        learner_id=request.learner_id,
        skill_scores=updated_scores,
        message=(
            f"Assessment complete! You already have solid knowledge in {completed_count} skill(s). "
            "Your personalised path has been calibrated accordingly."
        ),
    )
