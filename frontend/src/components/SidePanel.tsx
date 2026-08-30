/**
 * components/SidePanel.tsx — Sliding side panel for skill node details.
 * Shows: skill info, resources, "Why is this here?" explanation, action buttons.
 */

import { useState, useEffect } from "react";
import { X, ExternalLink, BookOpen, Play, FileText, Beaker, Brain, Loader2 } from "lucide-react";
import { api, type PathNode, type ResourceOut } from "../api";
import { useStore } from "../store/useStore";

interface SidePanelProps {
  node: PathNode | null;
  onClose: () => void;
  onRefresh: () => void;
}

const RESOURCE_ICON: Record<string, React.ReactNode> = {
  course:   <BookOpen size={14} />,
  video:    <Play size={14} />,
  article:  <FileText size={14} />,
  project:  <Beaker size={14} />,
  quiz:     <Brain size={14} />,
};

const RESOURCE_COLOR: Record<string, string> = {
  course:  "bg-blue-900/40 text-blue-300 border-blue-800",
  video:   "bg-red-900/40 text-red-300 border-red-800",
  article: "bg-gray-800/40 text-gray-300 border-gray-700",
  project: "bg-green-900/40 text-green-300 border-green-800",
  quiz:    "bg-purple-900/40 text-purple-300 border-purple-800",
};

export default function SidePanel({ node, onClose, onRefresh }: SidePanelProps) {
  const learnerId = useStore((s) => s.learnerId);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setExplanation(null);
    setMessage(null);
  }, [node?.skill_id]);

  if (!node) return null;

  const fetchExplanation = async () => {
    if (!learnerId) return;
    setLoadingExplain(true);
    try {
      const resp = await api.explainSkill(node.skill_id, learnerId);
      setExplanation(resp.explanation);
    } catch (e) {
      setExplanation("Could not load explanation. Please check the backend connection.");
    } finally {
      setLoadingExplain(false);
    }
  };

  const handleAction = async (eventType: string) => {
    if (!learnerId) return;
    setActionLoading(eventType);
    try {
      const resp = await api.progressEvent({
        learner_id: learnerId,
        skill_id: node.skill_id,
        event_type: eventType,
      });
      setMessage(resp.message);
      if (resp.replanned) {
        setTimeout(onRefresh, 1000);
      } else {
        onRefresh();
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const difficultyLabel = ["", "Beginner", "Elementary", "Intermediate", "Advanced", "Expert"];

  return (
    <div className="fixed right-0 top-0 h-full w-96 glass border-l border-gray-700 z-50 flex flex-col shadow-2xl">
      {/* Header */}
      <div className="flex items-start justify-between p-5 border-b border-gray-700">
        <div className="flex-1 pr-3">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${
              node.status === "completed"   ? "bg-emerald-900/40 text-emerald-300 border-emerald-700" :
              node.status === "in_progress" ? "bg-amber-900/40 text-amber-300 border-amber-700" :
              node.status === "unlocked"    ? "bg-brand-900/40 text-brand-300 border-brand-700" :
                                              "bg-gray-900/40 text-gray-400 border-gray-700"
            }`}>
              {node.status.replace("_", " ").toUpperCase()}
            </span>
            {node.is_milestone && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-900/40 text-yellow-300 border border-yellow-700">
                ★ MILESTONE
              </span>
            )}
          </div>
          <h2 className="text-lg font-bold text-white">{node.skill_name}</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {node.category} · {difficultyLabel[node.difficulty] ?? "Unknown"}
          </p>
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
          <X size={20} />
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Description */}
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">About</h3>
          <p className="text-sm text-gray-300 leading-relaxed">{node.description}</p>
        </div>

        {/* AI Explanation */}
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Why is this in my path?
          </h3>
          {explanation ? (
            <div className="bg-brand-950/50 border border-brand-800 rounded-xl p-3">
              <p className="text-sm text-brand-200 leading-relaxed">{explanation}</p>
            </div>
          ) : (
            <button
              onClick={fetchExplanation}
              disabled={loadingExplain}
              className="flex items-center gap-2 btn-secondary text-sm w-full justify-center"
            >
              {loadingExplain ? (
                <><Loader2 size={14} className="animate-spin" /> Asking AI...</>
              ) : (
                <><Brain size={14} /> Ask AI to Explain</>
              )}
            </button>
          )}
        </div>

        {/* Resources */}
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Learning Resources ({node.resources.length})
          </h3>
          {node.resources.length === 0 ? (
            <p className="text-sm text-gray-500">No resources linked yet.</p>
          ) : (
            <div className="space-y-2">
              {node.resources.map((r: ResourceOut) => (
                <a
                  key={r.id}
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`
                    block border rounded-lg p-3 hover:brightness-125 transition-all
                    ${RESOURCE_COLOR[r.type] ?? RESOURCE_COLOR.article}
                  `}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide opacity-70">
                      {RESOURCE_ICON[r.type]}
                      {r.type}
                    </div>
                    <div className="flex items-center gap-1 text-xs opacity-60">
                      <span>{r.est_hours}h</span>
                      <ExternalLink size={10} />
                    </div>
                  </div>
                  <p className="text-sm font-medium mt-1 leading-tight">{r.title}</p>
                </a>
              ))}
            </div>
          )}
        </div>

        {/* Message feedback */}
        {message && (
          <div className="bg-gray-800 border border-gray-600 rounded-xl p-3">
            <p className="text-sm text-gray-200">{message}</p>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="p-4 border-t border-gray-700 space-y-2">
        {node.status === "unlocked" && (
          <button
            onClick={() => handleAction("started")}
            disabled={!!actionLoading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {actionLoading === "started" ? <Loader2 size={16} className="animate-spin" /> : "🚀"}
            Start Learning
          </button>
        )}
        {node.status === "in_progress" && (
          <>
            <button
              onClick={() => handleAction("completed")}
              disabled={!!actionLoading}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {actionLoading === "completed" ? <Loader2 size={16} className="animate-spin" /> : "✅"}
              Mark Completed (+100 XP)
            </button>
            <button
              onClick={() => handleAction("failed_checkpoint")}
              disabled={!!actionLoading}
              className="btn-secondary w-full flex items-center justify-center gap-2 text-amber-400 border-amber-700"
            >
              {actionLoading === "failed_checkpoint" ? <Loader2 size={16} className="animate-spin" /> : "⚠️"}
              Failed Checkpoint (Re-plan)
            </button>
          </>
        )}
        {(node.status === "unlocked" || node.status === "locked") && (
          <button
            onClick={() => handleAction("skipped")}
            disabled={!!actionLoading}
            className="btn-secondary w-full flex items-center justify-center gap-2 text-sm"
          >
            {actionLoading === "skipped" ? <Loader2 size={16} className="animate-spin" /> : "⏭️"}
            Already Know This (Skip)
          </button>
        )}
      </div>
    </div>
  );
}
