"""
ai_client.py — Grok API wrapper for PathMind.
Uses the OpenAI Python SDK pointed at xAI's base URL.
All functions return structured data (JSON-mode prompts with fallback).
"""

import json
import os
import re
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_BASE_URL = "https://api.groq.com/openai/v1"
GROK_MODEL = "groq/compound"

# Fallback model if primary isn't available
FALLBACK_MODEL = "openai/gpt-oss-20b"

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not GROK_API_KEY:
            raise ValueError("GROK_API_KEY not set in environment / .env file")
        _client = OpenAI(api_key=GROK_API_KEY, base_url=GROK_BASE_URL)
    return _client


def _call_grok(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """Low-level call to Grok. Returns raw string content."""
    client = get_client()
    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.warning(f"Grok call failed with model {GROK_MODEL}, trying fallback: {e}")
        try:
            response = client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e2:
            logger.error(f"Fallback model also failed: {e2}")
            raise


def _parse_json(raw: str, fallback: Any) -> Any:
    """Extract JSON from a response string, with graceful fallback."""
    # Strip markdown code fences if present
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON object or array in the string
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    logger.warning(f"Could not parse JSON from Grok response, using fallback. Raw: {raw[:200]}")
    return fallback


# ---------------------------------------------------------------------------
# 1. extract_goals
# ---------------------------------------------------------------------------

def extract_goals(
    goal_text: str,
    interests: List[str],
    experience_level: str,
    available_skills: List[Dict],
) -> Dict:
    """
    Analyse the learner's free-text goal and return:
      - target_skills: list of skill names from available_skills that match the goal
      - diagnostic_questions: 5–7 adaptive quiz questions to assess current level
    """
    skills_list = "\n".join(
        f"- {s['name']} (category: {s['category']})" for s in available_skills
    )

    system = (
        "You are an expert learning path advisor. "
        "You MUST respond with ONLY valid JSON — no markdown, no prose before or after. "
        "Your JSON must match this exact schema:\n"
        "{\n"
        '  "target_skills": ["skill name 1", "skill name 2", ...],\n'
        '  "diagnostic_questions": [\n'
        "    {\n"
        '      "question_id": "q1",\n'
        '      "question_text": "...",\n'
        '      "skill_area": "skill name from the list",\n'
        '      "options": ["A) ...", "B) ...", "C) ...", "D) I don\'t know"]\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    user = (
        f"Learner goal: {goal_text}\n"
        f"Interests: {', '.join(interests) or 'not specified'}\n"
        f"Self-rated experience: {experience_level}\n\n"
        f"Available skills in the system:\n{skills_list}\n\n"
        "Select 8–15 target skills from the list above that are most relevant to this learner's goal. "
        "Then generate 6 diagnostic quiz questions (multiple-choice with 4 options) "
        "that probe the learner's current knowledge across different skill areas. "
        "Return ONLY the JSON object."
    )

    raw = _call_grok(system, user)
    fallback = {
        "target_skills": [s["name"] for s in available_skills[:10]],
        "diagnostic_questions": [
            {
                "question_id": "q1",
                "question_text": "How comfortable are you with Python programming?",
                "skill_area": "Python Basics",
                "options": ["A) Never used it", "B) Basic scripts", "C) Intermediate", "D) Advanced"],
            }
        ],
    }
    return _parse_json(raw, fallback)


# ---------------------------------------------------------------------------
# 2. score_quiz
# ---------------------------------------------------------------------------

def score_quiz(
    questions: List[Dict],
    answers: List[Dict],
    available_skills: List[Dict],
) -> Dict:
    """
    Score the diagnostic quiz answers and return confidence scores per skill.
    Returns: {"skill_scores": [{"skill_name": ..., "confidence": 0.0-1.0, "status": ...}]}
    """
    qa_pairs = []
    answer_map = {a["question_id"]: a["answer"] for a in answers}
    for q in questions:
        qa_pairs.append(
            f"Q ({q['skill_area']}): {q['question_text']}\n"
            f"  Options: {q.get('options', [])}\n"
            f"  Learner answered: {answer_map.get(q['question_id'], 'no answer')}"
        )

    skills_list = ", ".join(s["name"] for s in available_skills)

    system = (
        "You are an expert educational assessor. "
        "Respond with ONLY valid JSON matching this schema:\n"
        "{\n"
        '  "skill_scores": [\n'
        '    {"skill_name": "...", "confidence": 0.7, "status": "in_progress"}\n'
        "  ]\n"
        "}\n"
        "Status must be: 'unknown' (confidence < 0.3), 'in_progress' (0.3-0.79), or 'completed' (>=0.8)."
    )

    user = (
        f"Quiz answers:\n" + "\n".join(qa_pairs) + "\n\n"
        f"Available skills: {skills_list}\n\n"
        "For each skill area tested, estimate a confidence score (0.0–1.0) and status. "
        "Return ONLY the JSON."
    )

    raw = _call_grok(system, user)
    fallback = {
        "skill_scores": [
            {"skill_name": q["skill_area"], "confidence": 0.0, "status": "unknown"}
            for q in questions
        ]
    }
    return _parse_json(raw, fallback)


# ---------------------------------------------------------------------------
# 3. explain_skill
# ---------------------------------------------------------------------------

def explain_skill(
    skill_name: str,
    skill_description: str,
    skill_category: str,
    prerequisites: List[str],
    dependents: List[str],
    learner_goal: str,
    path_position: int,
    total_path_length: int,
) -> str:
    """
    Generate a grounded 2–3 sentence explanation of why this skill is in the learner's path.
    Explicitly cites the prerequisite graph relationships.
    """
    prereqs_text = ", ".join(prerequisites) if prerequisites else "none (this is a foundational skill)"
    dependents_text = ", ".join(dependents) if dependents else "none (this is an advanced terminal skill)"

    system = (
        "You are a concise learning advisor. Generate a 2–3 sentence explanation for why a specific "
        "skill is included in a personalized learning path. "
        "You MUST explicitly mention the prerequisite relationships by name — do not be generic. "
        "Respond with ONLY valid JSON: {\"explanation\": \"...your 2-3 sentences...\"}"
    )

    user = (
        f"Skill: {skill_name} (category: {skill_category})\n"
        f"Description: {skill_description}\n"
        f"This skill's prerequisites (skills it requires): {prereqs_text}\n"
        f"Skills that depend on this skill: {dependents_text}\n"
        f"Learner's goal: {learner_goal}\n"
        f"Position in path: {path_position} of {total_path_length}\n\n"
        "Write a grounded 2–3 sentence explanation citing the actual prerequisite names and "
        "how this skill connects to the learner's goal. Return ONLY the JSON."
    )

    raw = _call_grok(system, user, temperature=0.4)
    result = _parse_json(
        raw,
        {"explanation": f"{skill_name} is a key building block in your learning path toward your goal."},
    )
    return result.get("explanation", f"{skill_name} is essential for your learning journey.")


# ---------------------------------------------------------------------------
# 4. chat_response
# ---------------------------------------------------------------------------

def chat_response(
    learner_name: str,
    learner_goal: str,
    experience_level: str,
    current_path_summary: str,
    chat_history: List[Dict],
    new_message: str,
) -> str:
    """
    Generate an AI tutor reply grounded in the learner's profile and current path.
    """
    system = (
        f"You are PathMind AI Tutor — a knowledgeable, encouraging, and concise learning coach. "
        f"You are helping {learner_name} who wants to: {learner_goal}\n"
        f"Their experience level: {experience_level}\n"
        f"Their current learning path summary:\n{current_path_summary}\n\n"
        "Answer questions about their path, explain concepts, give study advice, and motivate them. "
        "Be specific — reference actual skills and resources from their path when relevant. "
        "Keep responses under 200 words unless the learner asks for a detailed explanation."
    )

    messages = [{"role": "system", "content": system}]
    # Include recent chat history (last 10 messages for context)
    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["message"]})
    messages.append({"role": "user", "content": new_message})

    client = get_client()
    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=messages,
            temperature=0.6,
            max_tokens=512,
        )
        return response.choices[0].message.content or "I'm here to help! Could you rephrase that?"
    except Exception as e:
        logger.error(f"Chat response failed: {e}")
        return "I'm temporarily unavailable. Please try again in a moment."


# ---------------------------------------------------------------------------
# 5. generate_weekly_plan (stretch goal)
# ---------------------------------------------------------------------------

def generate_weekly_plan(
    learner_name: str,
    learner_goal: str,
    next_skills: List[str],
    hours_per_week: int = 10,
) -> str:
    """Generate a weekly study plan text (stretch goal)."""
    system = (
        "You are a learning schedule advisor. Generate a structured weekly study plan. "
        "Respond with ONLY valid JSON: {\"weekly_plan\": \"...markdown-formatted plan...\"}"
    )
    user = (
        f"Learner: {learner_name}\n"
        f"Goal: {learner_goal}\n"
        f"Available hours per week: {hours_per_week}\n"
        f"Next skills to tackle: {', '.join(next_skills)}\n\n"
        "Create a day-by-day study plan for this week. Be specific with tasks and time allocations."
    )
    try:
        raw = _call_grok(system, user, temperature=0.5)
        result = _parse_json(raw, {"weekly_plan": "Focus on your next skill this week!"})
        return result.get("weekly_plan", "")
    except Exception:
        return ""
