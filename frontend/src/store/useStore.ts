/**
 * store/useStore.ts — Zustand global state for PathMind.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PathNode, DiagnosticQuestion } from "../api";

interface AppState {
  learnerId: number | null;
  learnerName: string;
  learnerGoal: string;
  pathNodes: PathNode[];
  targetSkills: string[];
  diagnosticQuestions: DiagnosticQuestion[];
  overallProgress: number;

  // Actions
  setLearner: (id: number, name: string, goal: string) => void;
  setPathNodes: (nodes: PathNode[]) => void;
  setTargetSkills: (skills: string[]) => void;
  setDiagnosticQuestions: (qs: DiagnosticQuestion[]) => void;
  setOverallProgress: (p: number) => void;
  updateNodeStatus: (
    skill_id: number,
    status: PathNode["status"]
  ) => void;
  clearSession: () => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      learnerId: null,
      learnerName: "",
      learnerGoal: "",
      pathNodes: [],
      targetSkills: [],
      diagnosticQuestions: [],
      overallProgress: 0,

      setLearner: (id, name, goal) =>
        set({ learnerId: id, learnerName: name, learnerGoal: goal }),

      setPathNodes: (nodes) => set({ pathNodes: nodes }),

      setTargetSkills: (skills) => set({ targetSkills: skills }),

      setDiagnosticQuestions: (qs) => set({ diagnosticQuestions: qs }),

      setOverallProgress: (p) => set({ overallProgress: p }),

      updateNodeStatus: (skill_id, status) =>
        set((state) => ({
          pathNodes: state.pathNodes.map((n) =>
            n.skill_id === skill_id ? { ...n, status } : n
          ),
        })),

      clearSession: () =>
        set({
          learnerId: null,
          learnerName: "",
          learnerGoal: "",
          pathNodes: [],
          targetSkills: [],
          diagnosticQuestions: [],
          overallProgress: 0,
        }),
    }),
    {
      name: "pathmind-session",
      partialize: (state) => ({
        learnerId: state.learnerId,
        learnerName: state.learnerName,
        learnerGoal: state.learnerGoal,
        overallProgress: state.overallProgress,
      }),
    }
  )
);
