/**
 * components/SkillNode.tsx — Custom React Flow node for PathMind skill tree.
 * Colored by status: locked/unlocked/in_progress/completed.
 */

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { PathNode } from "../api";

const STATUS_STYLES: Record<PathNode["status"], string> = {
  locked:      "bg-gray-900 border-gray-700 text-gray-500",
  unlocked:    "bg-brand-950 border-brand-500 text-brand-300 shadow-[0_0_12px_rgba(82,97,234,0.4)]",
  in_progress: "bg-amber-950 border-amber-400 text-amber-200 shadow-[0_0_12px_rgba(245,158,11,0.4)]",
  completed:   "bg-emerald-950 border-emerald-400 text-emerald-200 shadow-[0_0_12px_rgba(16,185,129,0.4)]",
};

const STATUS_ICON: Record<PathNode["status"], string> = {
  locked:      "🔒",
  unlocked:    "🔓",
  in_progress: "⚡",
  completed:   "✅",
};

const CATEGORY_COLORS: Record<string, string> = {
  Programming:      "bg-purple-900/40 text-purple-300",
  "Data Manipulation": "bg-blue-900/40 text-blue-300",
  Databases:        "bg-orange-900/40 text-orange-300",
  Mathematics:      "bg-pink-900/40 text-pink-300",
  Visualization:    "bg-cyan-900/40 text-cyan-300",
  "Machine Learning": "bg-indigo-900/40 text-indigo-300",
  "Deep Learning":  "bg-rose-900/40 text-rose-300",
  MLOps:            "bg-teal-900/40 text-teal-300",
  Capstone:         "bg-yellow-900/40 text-yellow-300",
};

export interface SkillNodeData extends PathNode {
  onClick: (node: PathNode) => void;
}

const SkillNode = memo(({ data }: NodeProps<SkillNodeData>) => {
  const statusStyle = STATUS_STYLES[data.status] ?? STATUS_STYLES.locked;
  const categoryStyle =
    CATEGORY_COLORS[data.category] ?? "bg-gray-800/40 text-gray-300";

  return (
    <>
      <Handle type="target" position={Position.Top} className="!bg-gray-600 !border-gray-500" />
      <div
        className={`
          relative border-2 rounded-xl px-3 py-2 cursor-pointer
          min-w-[130px] max-w-[160px] transition-all duration-200
          hover:scale-105 hover:brightness-110
          ${statusStyle}
          ${data.is_milestone ? "border-[3px]" : ""}
        `}
        onClick={() => data.onClick(data)}
      >
        {/* Milestone badge */}
        {data.is_milestone && (
          <div className="absolute -top-2 -right-2 text-xs bg-yellow-500 text-yellow-900 rounded-full w-5 h-5 flex items-center justify-center font-bold">
            ★
          </div>
        )}

        {/* Difficulty pips */}
        <div className="flex gap-0.5 mb-1">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className={`h-1 w-3 rounded-full ${
                i < data.difficulty ? "bg-current opacity-70" : "bg-gray-700"
              }`}
            />
          ))}
        </div>

        {/* Status icon + name */}
        <div className="flex items-start gap-1">
          <span className="text-sm leading-none mt-0.5">{STATUS_ICON[data.status]}</span>
          <p className="text-xs font-semibold leading-tight line-clamp-2">{data.skill_name}</p>
        </div>

        {/* Category tag */}
        <div className={`mt-1.5 text-[9px] font-medium px-1.5 py-0.5 rounded-full w-fit ${categoryStyle}`}>
          {data.category}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-600 !border-gray-500" />
    </>
  );
});

SkillNode.displayName = "SkillNode";
export default SkillNode;
