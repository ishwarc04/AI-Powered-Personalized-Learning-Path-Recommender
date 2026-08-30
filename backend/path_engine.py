"""
path_engine.py — networkx DAG engine for PathMind.
Computes minimal ordered learning paths and handles adaptive re-planning.
"""

import json
import logging
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def build_graph(db: Session) -> nx.DiGraph:
    """
    Build a directed graph from the skill_prereqs table.
    Edge direction: prereq_skill → skill  (prereq must come before skill)
    """
    from models import Skill, SkillPrereq

    G = nx.DiGraph()

    # Add all skill nodes
    skills = db.query(Skill).all()
    for skill in skills:
        G.add_node(
            skill.id,
            name=skill.name,
            category=skill.category,
            description=skill.description,
            difficulty=skill.difficulty,
        )

    # Add directed edges: prereq → skill
    prereqs = db.query(SkillPrereq).all()
    for prereq in prereqs:
        G.add_edge(prereq.prereq_skill_id, prereq.skill_id)

    return G


def _ancestors_of(G: nx.DiGraph, skill_ids: Set[int]) -> Set[int]:
    """Return all ancestor skill IDs needed to reach the given skill_ids."""
    ancestors = set()
    for sid in skill_ids:
        if sid in G:
            ancestors.update(nx.ancestors(G, sid))
    return ancestors


def compute_path(
    db: Session,
    G: nx.DiGraph,
    known_skill_ids: Set[int],
    target_skill_ids: Set[int],
) -> List[int]:
    """
    Compute the minimal ordered sequence of skill IDs the learner must complete
    to reach target_skill_ids from their current known_skill_ids.

    Algorithm:
    1. Find all ancestors of all target skills (the full prerequisite closure).
    2. Subtract skills already completed by the learner.
    3. Build the subgraph of remaining required skills.
    4. Topological-sort the subgraph to get the correct learning order.
    5. Append target skills at the end (if not already included via ancestors).
    """
    if not target_skill_ids:
        return []

    # All skills needed (ancestors + targets)
    needed = _ancestors_of(G, target_skill_ids) | target_skill_ids

    # Remove skills the learner already knows
    needed -= known_skill_ids

    if not needed:
        logger.info("Learner already knows all needed skills!")
        return []

    # Build subgraph of only the needed nodes
    sub = G.subgraph(needed).copy()

    # Handle nodes that might not be in the graph
    needed = needed & set(G.nodes())
    sub = G.subgraph(needed).copy()

    try:
        ordered = list(nx.topological_sort(sub))
    except nx.NetworkXUnfeasible:
        logger.error("Cycle detected in skill prerequisite graph!")
        # Return a best-effort ordering using all nodes
        ordered = list(needed)

    return ordered


def get_learner_known_skills(db: Session, learner_id: int) -> Set[int]:
    """Return the set of skill IDs the learner has completed."""
    from models import LearnerSkill

    rows = (
        db.query(LearnerSkill)
        .filter(
            LearnerSkill.learner_id == learner_id,
            LearnerSkill.status == "completed",
        )
        .all()
    )
    return {row.skill_id for row in rows}


def get_learner_target_skills(db: Session, learner_id: int) -> Tuple[Set[int], List[str]]:
    """
    Return the learner's target skill IDs from their most recent active learning path.
    Also returns the list of target skill names for reference.
    """
    from models import LearningPath, Skill

    path = (
        db.query(LearningPath)
        .filter(LearningPath.learner_id == learner_id, LearningPath.status == "active")
        .order_by(LearningPath.generated_at.desc())
        .first()
    )
    if not path:
        return set(), []

    target_names = path.target_skills
    skills = db.query(Skill).filter(Skill.name.in_(target_names)).all()
    return {s.id for s in skills}, target_names


def build_path_nodes(
    db: Session,
    G: nx.DiGraph,
    ordered_skill_ids: List[int],
    known_skill_ids: Set[int],
    learner_skill_map: Dict[int, str],  # skill_id -> status
) -> List[Dict]:
    """
    Convert an ordered list of skill IDs into a list of PathNode dicts
    with status (locked/unlocked/in_progress/completed) and resources.
    """
    from models import Skill, Resource, SkillPrereq

    # Pre-fetch all skills and resources in one query
    skill_map = {s.id: s for s in db.query(Skill).filter(Skill.id.in_(ordered_skill_ids)).all()}
    resource_map: Dict[int, List] = {}
    for res in db.query(Resource).filter(Resource.skill_id.in_(ordered_skill_ids)).all():
        resource_map.setdefault(res.skill_id, []).append(res)

    completed_set = {sid for sid, st in learner_skill_map.items() if st == "completed"}
    in_progress_set = {sid for sid, st in learner_skill_map.items() if st == "in_progress"}

    nodes = []
    for pos, sid in enumerate(ordered_skill_ids):
        skill = skill_map.get(sid)
        if not skill:
            continue

        # Determine status
        if sid in completed_set or sid in known_skill_ids:
            status = "completed"
        elif sid in in_progress_set:
            status = "in_progress"
        else:
            # Unlocked if all prerequisites are completed
            prereqs_in_path = [pred for pred in G.predecessors(sid) if pred in set(ordered_skill_ids)]
            prereqs_done = all(p in completed_set or p in known_skill_ids for p in prereqs_in_path)
            if prereqs_done:
                status = "unlocked"
            else:
                status = "locked"

        resources = [
            {
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "difficulty": r.difficulty,
                "url": r.url,
                "est_hours": r.est_hours,
            }
            for r in resource_map.get(sid, [])
        ]

        # Mark every 5th node as a milestone
        is_milestone = (pos + 1) % 5 == 0 or sid in {ordered_skill_ids[-1]} if ordered_skill_ids else False

        nodes.append(
            {
                "skill_id": sid,
                "skill_name": skill.name,
                "category": skill.category,
                "description": skill.description,
                "difficulty": skill.difficulty,
                "status": status,
                "position": pos,
                "resources": resources,
                "is_milestone": is_milestone,
                "prereq_skill_ids": list(G.predecessors(sid)),
            }
        )

    return nodes


def replan(db: Session, learner_id: int) -> Optional[List[Dict]]:
    """
    Re-generate the learning path for a learner based on their current skill status.
    Updates the active LearningPath record in the DB.
    Returns the new list of PathNode dicts (or None on failure).
    """
    from models import LearningPath, LearnerSkill

    G = build_graph(db)
    known_ids = get_learner_known_skills(db, learner_id)
    target_ids, target_names = get_learner_target_skills(db, learner_id)

    if not target_ids:
        logger.warning(f"No target skills for learner {learner_id}, cannot replan.")
        return None

    ordered = compute_path(db, G, known_ids, target_ids)

    # Update the active path record
    path = (
        db.query(LearningPath)
        .filter(LearningPath.learner_id == learner_id, LearningPath.status == "active")
        .order_by(LearningPath.generated_at.desc())
        .first()
    )

    if not path:
        from datetime import datetime
        path = LearningPath(learner_id=learner_id, status="active")
        path.target_skills = target_names
        db.add(path)

    # Build learner skill map
    learner_skill_rows = db.query(LearnerSkill).filter(LearnerSkill.learner_id == learner_id).all()
    learner_skill_map = {row.skill_id: row.status for row in learner_skill_rows}

    nodes = build_path_nodes(db, G, ordered, known_ids, learner_skill_map)
    path.path_json = nodes
    db.commit()
    db.refresh(path)

    return nodes


def insert_remedial_node(
    db: Session,
    learner_id: int,
    failed_skill_id: int,
) -> bool:
    """
    When a learner fails a checkpoint for a skill, insert easier prerequisite resources
    or mark prerequisite skills as needing review (lower their confidence score).
    Returns True if re-plan was triggered.
    """
    from models import LearnerSkill

    # Reduce confidence for the failed skill
    ls = (
        db.query(LearnerSkill)
        .filter(LearnerSkill.learner_id == learner_id, LearnerSkill.skill_id == failed_skill_id)
        .first()
    )
    if ls:
        ls.confidence_score = max(0.0, (ls.confidence_score or 0.5) - 0.3)
        ls.status = "in_progress"
        db.commit()

    # Re-plan to re-include the skill and its prerequisites
    replan(db, learner_id)
    return True
