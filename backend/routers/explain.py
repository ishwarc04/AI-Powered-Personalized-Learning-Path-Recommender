"""
routers/explain.py — POST /explain/{skill_id}
Generates a grounded "why is this skill in my path?" explanation via Grok.
Caches results in skill_explanation_cache to avoid repeated API calls.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Skill, SkillPrereq, Learner, LearningPath, SkillExplanationCache
import ai_client
import schemas

router = APIRouter(prefix="/api", tags=["Explain"])


@router.post("/explain/{skill_id}", response_model=schemas.ExplainResponse)
def explain_skill(
    skill_id: int,
    request: schemas.ExplainRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a grounded 2–3 sentence explanation of why a specific skill is
    in the learner's path. Explanation cites actual prerequisite graph edges.
    Results are cached per (learner_id, skill_id).
    """
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    learner = db.query(Learner).filter(Learner.id == request.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Check cache
    cached = (
        db.query(SkillExplanationCache)
        .filter(
            SkillExplanationCache.learner_id == request.learner_id,
            SkillExplanationCache.skill_id == skill_id,
        )
        .first()
    )
    if cached:
        return schemas.ExplainResponse(
            skill_id=skill_id,
            skill_name=skill.name,
            explanation=cached.explanation,
            cached=True,
        )

    # Get prerequisite names (skills THIS skill requires)
    prereq_links = (
        db.query(SkillPrereq)
        .filter(SkillPrereq.skill_id == skill_id)
        .all()
    )
    prereq_ids = [p.prereq_skill_id for p in prereq_links]
    prereq_skills = db.query(Skill).filter(Skill.id.in_(prereq_ids)).all()
    prereq_names = [s.name for s in prereq_skills]

    # Get dependents (skills that require THIS skill)
    dependent_links = (
        db.query(SkillPrereq)
        .filter(SkillPrereq.prereq_skill_id == skill_id)
        .all()
    )
    dependent_ids = [d.skill_id for d in dependent_links]
    dependent_skills = db.query(Skill).filter(Skill.id.in_(dependent_ids)).all()
    dependent_names = [s.name for s in dependent_skills]

    # Get path position
    lp = (
        db.query(LearningPath)
        .filter(
            LearningPath.learner_id == request.learner_id,
            LearningPath.status == "active",
        )
        .order_by(LearningPath.generated_at.desc())
        .first()
    )
    path_nodes = lp.path_json if lp else []
    path_position = next(
        (n["position"] for n in path_nodes if n["skill_id"] == skill_id), 0
    )
    total_path_length = len(path_nodes)

    try:
        explanation = ai_client.explain_skill(
            skill_name=skill.name,
            skill_description=skill.description,
            skill_category=skill.category,
            prerequisites=prereq_names,
            dependents=dependent_names,
            learner_goal=learner.goals_text,
            path_position=path_position,
            total_path_length=total_path_length,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    # Cache the result
    cache_entry = SkillExplanationCache(
        learner_id=request.learner_id,
        skill_id=skill_id,
        explanation=explanation,
    )
    db.add(cache_entry)
    db.commit()

    return schemas.ExplainResponse(
        skill_id=skill_id,
        skill_name=skill.name,
        explanation=explanation,
        cached=False,
    )
