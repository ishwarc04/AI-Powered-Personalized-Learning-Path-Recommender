/**
 * api.ts — Typed fetch wrapper for all PathMind backend endpoints.
 */

const BASE_URL = "/api";

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface DiagnosticQuestion {
  question_id: string;
  question_text: string;
  skill_area: string;
  options: string[] | null;
}

export interface OnboardResponse {
  learner_id: number;
  target_skills: string[];
  diagnostic_questions: DiagnosticQuestion[];
  message: string;
}

export interface SkillScore {
  skill_name: string;
  confidence: number;
  status: string;
}

export interface DiagnosticQuizResponse {
  learner_id: number;
  skill_scores: SkillScore[];
  message: string;
}

export interface ResourceOut {
  id: number;
  title: string;
  type: string;
  difficulty: number;
  url: string;
  est_hours: number;
}

export interface PathNode {
  skill_id: number;
  skill_name: string;
  category: string;
  description: string;
  difficulty: number;
  status: "locked" | "unlocked" | "in_progress" | "completed";
  position: number;
  resources: ResourceOut[];
  is_milestone: boolean;
  prereq_skill_ids: number[];
}

export interface GeneratePathResponse {
  learner_id: number;
  path_id: number;
  nodes: PathNode[];
  total_estimated_hours: number;
  message: string;
}

export interface PathResponse {
  learner_id: number;
  path_id: number | null;
  nodes: PathNode[];
  overall_progress: number;
  total_estimated_hours: number;
}

export interface ExplainResponse {
  skill_id: number;
  skill_name: string;
  explanation: string;
  cached: boolean;
}

export interface ChatResponse {
  learner_id: number;
  reply: string;
  timestamp: string;
}

export interface ProgressEventResponse {
  event_id: number;
  replanned: boolean;
  message: string;
  updated_nodes: PathNode[] | null;
}

export interface CategoryStat {
  category: string;
  total_skills: number;
  completed_skills: number;
  pct: number;
}

export interface RecommendedAction {
  type: string;
  skill_name: string;
  resource_title?: string;
  resource_url?: string;
  resource_type?: string;
  reason: string;
}

export interface Badge {
  name: string;
  description: string;
  icon: string;
  earned_at: string | null;
}

export interface DashboardResponse {
  learner_id: number;
  learner_name: string;
  overall_progress: number;
  completed_skills: number;
  total_skills_in_path: number;
  xp_points: number;
  streak_days: number;
  total_hours_spent: number;
  category_stats: CategoryStat[];
  recommended_actions: RecommendedAction[];
  badges: Badge[];
  weekly_plan: string | null;
}

// ── API Functions ─────────────────────────────────────────────────────────────

export const api = {
  onboard: (payload: {
    name: string;
    goal_text: string;
    interests: string[];
    experience_level: string;
  }) => request<OnboardResponse>("POST", "/onboard", payload),

  diagnosticQuiz: (payload: {
    learner_id: number;
    answers: { question_id: string; answer: string }[];
  }) => request<DiagnosticQuizResponse>("POST", "/diagnostic-quiz", payload),

  generatePath: (learner_id: number) =>
    request<GeneratePathResponse>("POST", "/generate-path", { learner_id }),

  getPath: (learner_id: number) =>
    request<PathResponse>("GET", `/path/${learner_id}`),

  explainSkill: (skill_id: number, learner_id: number) =>
    request<ExplainResponse>("POST", `/explain/${skill_id}`, { learner_id }),

  chat: (learner_id: number, message: string) =>
    request<ChatResponse>("POST", "/chat", { learner_id, message }),

  progressEvent: (payload: {
    learner_id: number;
    resource_id?: number;
    skill_id?: number;
    event_type: string;
    metadata?: Record<string, unknown>;
  }) => request<ProgressEventResponse>("POST", "/progress-event", payload),

  getDashboard: (learner_id: number) =>
    request<DashboardResponse>("GET", `/dashboard/${learner_id}`),
};
