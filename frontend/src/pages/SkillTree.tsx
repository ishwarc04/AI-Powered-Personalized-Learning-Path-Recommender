/**
 * pages/SkillTree.tsx — Interactive React Flow skill tree (RPG-style DAG).
 * Nodes colored by status. Side panel opens on click.
 */

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";

import { api, type PathNode } from "../api";
import { useStore } from "../store/useStore";
import SkillNode, { type SkillNodeData } from "../components/SkillNode";
import SidePanel from "../components/SidePanel";
import TutorChat from "../components/TutorChat";
import { RefreshCw, LayoutDashboard, Loader2 } from "lucide-react";

const nodeTypes = { skillNode: SkillNode };

// Status → minimap color
const STATUS_COLOR: Record<string, string> = {
  locked:      "#374151",
  unlocked:    "#3d46d9",
  in_progress: "#d97706",
  completed:   "#059669",
};

function buildLayout(pathNodes: PathNode[]): { nodes: Node[]; edges: Edge[] } {
  const colWidth = 200;
  const rowHeight = 150;

  // 1. Calculate DAG depth for each node
  const depthMap: Record<number, number> = {};
  const pathSkillIds = new Set(pathNodes.map(n => n.skill_id));

  // Initialize depths
  pathNodes.forEach(n => depthMap[n.skill_id] = 0);

  // Run relaxation algorithm to find longest path from any source
  let changed = true;
  for (let iter = 0; iter < 100 && changed; iter++) {
    changed = false;
    for (const n of pathNodes) {
      let maxPrereqDepth = -1;
      for (const pid of n.prereq_skill_ids) {
        if (pathSkillIds.has(pid)) {
          maxPrereqDepth = Math.max(maxPrereqDepth, depthMap[pid]);
        }
      }
      const newDepth = maxPrereqDepth + 1;
      if (depthMap[n.skill_id] !== newDepth) {
        depthMap[n.skill_id] = newDepth;
        changed = true;
      }
    }
  }

  // 2. Group nodes by depth
  const depthGroups: Record<number, PathNode[]> = {};
  pathNodes.forEach(n => {
    const d = depthMap[n.skill_id] || 0;
    if (!depthGroups[d]) depthGroups[d] = [];
    depthGroups[d].push(n);
  });

  // Sort nodes within each depth group by category/name to maintain order
  Object.keys(depthGroups).forEach(dStr => {
    const d = Number(dStr);
    depthGroups[d].sort((a, b) => a.category.localeCompare(b.category) || a.skill_name.localeCompare(b.skill_name));
  });

  // 3. Generate layout coordinates (centered horizontally)
  const nodes: Node<SkillNodeData>[] = [];
  Object.entries(depthGroups).forEach(([depthStr, group]) => {
    const depth = Number(depthStr);
    const count = group.length;
    group.forEach((n, index) => {
      // Center position calculation
      const x = (index - (count - 1) / 2) * colWidth;
      const y = depth * rowHeight;

      nodes.push({
        id: String(n.skill_id),
        type: "skillNode",
        position: { x, y },
        data: {
          ...n,
          onClick: () => {}, // Overridden dynamically in component
        },
      });
    });
  });

  // 4. Generate edges
  const edges: Edge[] = [];
  pathNodes.forEach((n) => {
    n.prereq_skill_ids.forEach((prereqId) => {
      if (pathSkillIds.has(prereqId)) {
        edges.push({
          id: `${prereqId}-${n.skill_id}`,
          source: String(prereqId),
          target: String(n.skill_id),
          animated: n.status === "in_progress",
          type: "smoothstep",
          style: {
            stroke:
              n.status === "completed" ? "#10b981" :
              n.status === "in_progress" ? "#f59e0b" :
              n.status === "unlocked" ? "#5261ea" :
              "#374151",
            strokeWidth: 2,
          },
        });
      }
    });
  });

  return { nodes, edges };
}

export default function SkillTree() {
  const navigate = useNavigate();
  const learnerId = useStore((s) => s.learnerId);
  const storedNodes = useStore((s) => s.pathNodes);
  const setPathNodes = useStore((s) => s.setPathNodes);
  const setOverallProgress = useStore((s) => s.setOverallProgress);

  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<PathNode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const handleNodeClick = useCallback((node: PathNode) => {
    setSelectedNode(node);
  }, []);

  const applyNodes = useCallback(
    (pathNodes: PathNode[]) => {
      const { nodes: rfNodes, edges: rfEdges } = buildLayout(pathNodes);
      // Inject onClick
      setNodes(
        rfNodes.map((n) => ({
          ...n,
          data: {
            ...n.data,
            onClick: handleNodeClick,
          },
        }))
      );
      setEdges(rfEdges);
    },
    [handleNodeClick]
  );

  const fetchPath = useCallback(async () => {
    if (!learnerId) {
      navigate("/");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const resp = await api.getPath(learnerId);
      setPathNodes(resp.nodes);
      setProgress(resp.overall_progress);
      setOverallProgress(resp.overall_progress);
      applyNodes(resp.nodes);

      // Update selected node data if panel is open
      if (selectedNode) {
        const updated = resp.nodes.find((n) => n.skill_id === selectedNode.skill_id);
        if (updated) setSelectedNode(updated);
      }
    } catch (e: any) {
      // If no path exists, try to generate one
      if (e.message?.includes("No active learning path")) {
        try {
          const genResp = await api.generatePath(learnerId);
          setPathNodes(genResp.nodes);
          applyNodes(genResp.nodes);
        } catch (e2: any) {
          setError(e2.message);
        }
      } else {
        setError(e.message);
      }
    } finally {
      setLoading(false);
    }
  }, [learnerId, navigate, selectedNode, applyNodes]);

  useEffect(() => {
    if (storedNodes.length > 0) {
      applyNodes(storedNodes);
      setProgress(useStore.getState().overallProgress);
    }
    fetchPath();
  }, []);

  const completedCount = storedNodes.filter((n) => n.status === "completed").length;
  const totalCount = storedNodes.length;

  if (!learnerId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">No active session. Please onboard first.</p>
          <button onClick={() => navigate("/")} className="btn-primary">
            Start Onboarding
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Top bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800 glass z-10">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-black text-white">
            Path<span className="text-brand-400">Mind</span>
          </h1>
          <span className="text-gray-500 text-sm">Skill Tree</span>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-32 bg-gray-800 rounded-full h-2">
              <div
                className="bg-brand-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
            <span className="text-sm text-gray-300">
              {completedCount}/{totalCount} skills
            </span>
          </div>

          <button
            onClick={fetchPath}
            disabled={loading}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            Refresh
          </button>

          <button
            onClick={() => navigate("/dashboard")}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <LayoutDashboard size={14} />
            Dashboard
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 px-5 py-2 border-b border-gray-800 bg-gray-900/50 text-xs">
        {[
          { color: "bg-gray-600", label: "🔒 Locked" },
          { color: "bg-brand-600", label: "🔓 Unlocked" },
          { color: "bg-amber-500", label: "⚡ In Progress" },
          { color: "bg-emerald-500", label: "✅ Completed" },
          { color: "bg-yellow-500", label: "★ Milestone" },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1.5 text-gray-400">
            <div className={`w-2.5 h-2.5 rounded-sm ${item.color}`} />
            {item.label}
          </div>
        ))}
        <span className="ml-auto text-gray-600">Click any node to see details & actions</span>
      </div>

      {/* Error state */}
      {error && (
        <div className="mx-5 mt-3 bg-red-900/30 border border-red-700 rounded-xl p-3 text-sm text-red-300">
          {error}. Make sure the backend is running: <code>uvicorn main:app --reload</code>
        </div>
      )}

      {/* React Flow */}
      <div className="flex-1 relative">
        {loading && nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center z-20">
            <div className="flex flex-col items-center gap-3">
              <Loader2 size={40} className="animate-spin text-brand-400" />
              <p className="text-gray-400">Building your skill tree...</p>
            </div>
          </div>
        )}

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          minZoom={0.3}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={30}
            size={1}
            color="#1f2937"
          />
          <Controls className="!bg-gray-800 !border-gray-700" />
          <MiniMap
            nodeColor={(n) => STATUS_COLOR[(n.data as SkillNodeData)?.status ?? "locked"]}
            className="!bg-gray-900 !border-gray-700"
            maskColor="rgba(0,0,0,0.5)"
          />
        </ReactFlow>

        {/* Side Panel */}
        <SidePanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          onRefresh={fetchPath}
        />
      </div>

      <TutorChat />
    </div>
  );
}
