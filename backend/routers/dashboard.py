"""
routers/dashboard.py — GET /dashboard/{learner_id}
Aggregated stats: progress, radar chart data, streak, XP, recommended actions, badges, weekly plan.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Learner, LearningPath, LearnerSkill, ProgressEvent, Resource, Skill
import ai_client
import schemas

router = APIRouter(prefix="/api", tags=["Dashboard"])

BADGE_DEFINITIONS = [
    ("first_step",    "First Step",     "Completed your first skill",       "🎯"),
    ("on_a_roll",     "On a Roll",      "Completed 5 or more skills",       "🔥"),
    ("halfway_there", "Halfway There",  "Path is 50%+ complete",            "⚡"),
    ("deep_diver",    "Deep Diver",     "Completed a difficulty-5 skill",   "🏆"),
    ("consistent",    "Consistent",     "Achieved a 3-day streak",          "📅"),
    ("speed_learner", "Speed Learner",  "Completed 10+ skills",             "💨"),
]


def _compute_badges(
    completed_skills: int,
    path_pct: float,
    streak: int,
    has_diff5: bool,
) -> list:
    badges = []
    if completed_skills >= 1:
        badges.append({"name": "First Step", "description": "Completed your first skill", "icon": "🎯", "earned_at": None})
    if completed_skills >= 5:
        badges.append({"name": "On a Roll", "description": "Completed 5 or more skills", "icon": "🔥", "earned_at": None})
    if path_pct >= 0.5:
        badges.append({"name": "Halfway There", "description": "Path is 50%+ complete", "icon": "⚡", "earned_at": None})
    if has_diff5:
        badges.append({"name": "Deep Diver", "description": "Completed a difficulty-5 skill", "icon": "🏆", "earned_at": None})
    if streak >= 3:
        badges.append({"name": "Consistent", "description": "Achieved a 3-day streak", "icon": "📅", "earned_at": None})
    if completed_skills >= 10:
        badges.append({"name": "Speed Learner", "description": "Completed 10+ skills", "icon": "💨", "earned_at": None})
    return badges


@router.get("/dashboard/{learner_id}", response_model=schemas.DashboardResponse)
def get_dashboard(learner_id: int, db: Session = Depends(get_db)):
    """Return aggregated learning stats for the dashboard."""
    learner = db.query(Learner).filter(Learner.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Active path
    lp = (
        db.query(LearningPath)
        .filter(LearningPath.learner_id == learner_id, LearningPath.status == "active")
        .order_by(LearningPath.generated_at.desc())
        .first()
    )

    path_nodes = lp.path_json if lp else []
    total_in_path = len(path_nodes)
    completed_skills = sum(1 for n in path_nodes if n["status"] == "completed")
    overall_progress = completed_skills / total_in_path if total_in_path > 0 else 0.0

    # Category radar stats
    category_map: dict = {}
    for node in path_nodes:
        cat = node.get("category", "Other")
        if cat not in category_map:
            category_map[cat] = {"total": 0, "completed": 0}
        category_map[cat]["total"] += 1
        if node["status"] == "completed":
            category_map[cat]["completed"] += 1

    category_stats = [
        schemas.CategoryStat(
            category=cat,
            total_skills=vals["total"],
            completed_skills=vals["completed"],
            pct=round(vals["completed"] / vals["total"], 3) if vals["total"] > 0 else 0.0,
        )
        for cat, vals in category_map.items()
    ]

    # Time spent estimate (sum of est_hours for completed resource events)
    completed_resource_ids = [
        e.resource_id
        for e in db.query(ProgressEvent)
        .filter(
            ProgressEvent.learner_id == learner_id,
            ProgressEvent.event_type == "completed",
            ProgressEvent.resource_id.isnot(None),
        )
        .all()
    ]
    total_hours = 0.0
    if completed_resource_ids:
        resources = db.query(Resource).filter(Resource.id.in_(completed_resource_ids)).all()
        total_hours = sum(r.est_hours for r in resources)

    # Recommended next 3 actions
    recommended = []
    unlocked_nodes = [n for n in path_nodes if n["status"] == "unlocked"][:3]
    for node in unlocked_nodes:
        resources = node.get("resources", [])
        if resources:
            r = resources[0]
            recommended.append(
                schemas.RecommendedAction(
                    type="start_resource",
                    skill_name=node["skill_name"],
                    resource_title=r["title"],
                    resource_url=r["url"],
                    resource_type=r["type"],
                    reason=f"Next skill in your path: {node['skill_name']} (position {node['position']+1})",
                )
            )
        else:
            recommended.append(
                schemas.RecommendedAction(
                    type="review_skill",
                    skill_name=node["skill_name"],
                    reason=f"{node['skill_name']} is now unlocked and ready to start.",
                )
            )

    # Badges
    completed_skill_ids = [n["skill_id"] for n in path_nodes if n["status"] == "completed"]
    has_diff5 = False
    if completed_skill_ids:
        diff5_skills = db.query(Skill).filter(
            Skill.id.in_(completed_skill_ids), Skill.difficulty == 5
        ).count()
        has_diff5 = diff5_skills > 0

    badge_dicts = _compute_badges(
        completed_skills=completed_skills,
        path_pct=overall_progress,
        streak=learner.streak_days or 0,
        has_diff5=has_diff5,
    )
    badges = [schemas.Badge(**b) for b in badge_dicts]

    # Weekly plan (stretch goal — generate for free via LLM)
    weekly_plan = None
    if unlocked_nodes:
        try:
            next_skills = [n["skill_name"] for n in unlocked_nodes]
            weekly_plan = ai_client.generate_weekly_plan(
                learner_name=learner.name,
                learner_goal=learner.goals_text,
                next_skills=next_skills,
            )
        except Exception:
            weekly_plan = None

    return schemas.DashboardResponse(
        learner_id=learner_id,
        learner_name=learner.name,
        overall_progress=round(overall_progress, 3),
        completed_skills=completed_skills,
        total_skills_in_path=total_in_path,
        xp_points=learner.xp_points or 0,
        streak_days=learner.streak_days or 0,
        total_hours_spent=round(total_hours, 1),
        category_stats=category_stats,
        recommended_actions=recommended,
        badges=badges,
        weekly_plan=weekly_plan,
    )
