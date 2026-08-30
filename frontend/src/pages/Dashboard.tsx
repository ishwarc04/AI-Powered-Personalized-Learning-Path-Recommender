/**
 * pages/Dashboard.tsx — Learning analytics dashboard.
 * Recharts: radar chart of skill categories, progress bar, streak, XP, badges, recommended actions.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
} from "recharts";
import { Loader2, ArrowLeft, Flame, Zap, Trophy, ExternalLink } from "lucide-react";
import { api, type DashboardResponse } from "../api";
import { useStore } from "../store/useStore";
import TutorChat from "../components/TutorChat";

export default function Dashboard() {
  const navigate = useNavigate();
  const learnerId = useStore((s) => s.learnerId);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!learnerId) {
      navigate("/");
      return;
    }
    api.getDashboard(learnerId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [learnerId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 size={40} className="animate-spin text-brand-400" />
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-2">Error loading dashboard: {error}</p>
          <button onClick={() => navigate("/tree")} className="btn-secondary">← Back to Skill Tree</button>
        </div>
      </div>
    );
  }

  const radarData = data.category_stats.map((s) => ({
    category: s.category,
    completed: Math.round(s.pct * 100),
    fullMark: 100,
  }));

  return (
    <div className="min-h-screen grid-bg">
      {/* Header */}
      <div className="border-b border-gray-800 glass px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate("/tree")} className="text-gray-400 hover:text-white transition-colors">
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-xl font-black text-white">
            Path<span className="text-brand-400">Mind</span>
          </h1>
          <span className="text-gray-500 text-sm">Dashboard</span>
        </div>
        <p className="text-gray-400 text-sm">
          Welcome back, <span className="text-white font-semibold">{data.learner_name}</span>!
        </p>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            {
              label: "Overall Progress",
              value: `${Math.round(data.overall_progress * 100)}%`,
              sub: `${data.completed_skills} / ${data.total_skills_in_path} skills`,
              icon: <Zap size={20} className="text-brand-400" />,
              color: "from-brand-900/40 to-brand-950/60",
            },
            {
              label: "XP Points",
              value: data.xp_points.toLocaleString(),
              sub: "Keep going!",
              icon: <Trophy size={20} className="text-yellow-400" />,
              color: "from-yellow-900/20 to-yellow-950/40",
            },
            {
              label: "Day Streak",
              value: `${data.streak_days} 🔥`,
              sub: "days in a row",
              icon: <Flame size={20} className="text-orange-400" />,
              color: "from-orange-900/20 to-orange-950/40",
            },
            {
              label: "Hours Spent",
              value: `${data.total_hours_spent}h`,
              sub: "total learning time",
              icon: <span className="text-xl">⏱️</span>,
              color: "from-teal-900/20 to-teal-950/40",
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className={`glass rounded-2xl p-5 bg-gradient-to-br ${stat.color}`}
            >
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-400 uppercase tracking-wider">{stat.label}</p>
                {stat.icon}
              </div>
              <p className="text-3xl font-black text-white">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-1">{stat.sub}</p>
            </div>
          ))}
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Radar chart */}
          <div className="lg:col-span-2 glass rounded-2xl p-6">
            <h2 className="text-lg font-bold text-white mb-4">Skill Radar by Category</h2>
            {radarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <RadarChart data={radarData} margin={{ top: 10, right: 40, bottom: 10, left: 40 }}>
                  <PolarGrid stroke="#2a2a4a" />
                  <PolarAngleAxis
                    dataKey="category"
                    tick={{ fill: "#8888aa", fontSize: 11 }}
                  />
                  <PolarRadiusAxis
                    angle={30}
                    domain={[0, 100]}
                    tick={{ fill: "#555577", fontSize: 10 }}
                    tickCount={4}
                  />
                  <Radar
                    name="Completed %"
                    dataKey="completed"
                    stroke="#5261ea"
                    fill="#5261ea"
                    fillOpacity={0.3}
                    dot={{ fill: "#5261ea", r: 4 }}
                  />
                  <Tooltip
                    contentStyle={{ background: "#1a1a2e", border: "1px solid #2a2a4a", borderRadius: 12 }}
                    labelStyle={{ color: "#e0e0ff" }}
                    formatter={(value) => [`${Number(value)}%`, "Completed"]}
                  />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                Complete some skills to see your radar chart!
              </div>
            )}

            {/* Category breakdown */}
            <div className="mt-4 space-y-2">
              {data.category_stats.map((cat) => (
                <div key={cat.category} className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-36 truncate">{cat.category}</span>
                  <div className="flex-1 bg-gray-800 rounded-full h-1.5">
                    <div
                      className="bg-brand-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${cat.pct * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-16 text-right">
                    {cat.completed_skills}/{cat.total_skills}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Right column */}
          <div className="space-y-5">
            {/* Overall progress bar */}
            <div className="glass rounded-2xl p-5">
              <h2 className="text-sm font-bold text-white mb-3">Path Progress</h2>
              <div className="relative">
                <div className="bg-gray-800 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-4 rounded-full bg-gradient-to-r from-brand-600 to-brand-400 transition-all duration-700"
                    style={{ width: `${data.overall_progress * 100}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Start</span>
                  <span className="text-brand-400 font-semibold">
                    {Math.round(data.overall_progress * 100)}%
                  </span>
                  <span>Goal</span>
                </div>
              </div>
            </div>

            {/* Badges */}
            <div className="glass rounded-2xl p-5">
              <h2 className="text-sm font-bold text-white mb-3">
                Badges ({data.badges.length})
              </h2>
              {data.badges.length === 0 ? (
                <p className="text-xs text-gray-500">Complete skills to earn badges!</p>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  {data.badges.map((badge) => (
                    <div
                      key={badge.name}
                      className="bg-gray-800 border border-gray-700 rounded-xl p-2.5 text-center"
                    >
                      <p className="text-2xl mb-1">{badge.icon}</p>
                      <p className="text-xs font-semibold text-white">{badge.name}</p>
                      <p className="text-[10px] text-gray-500">{badge.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recommended actions */}
        <div className="glass rounded-2xl p-6">
          <h2 className="text-lg font-bold text-white mb-4">📋 Recommended Next Actions</h2>
          {data.recommended_actions.length === 0 ? (
            <p className="text-gray-500">All current skills completed! Generate a new path to continue.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {data.recommended_actions.map((action, i) => (
                <div
                  key={i}
                  className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 hover:border-brand-600 transition-all"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-xs text-brand-400 font-medium uppercase tracking-wide">
                      {action.type.replace(/_/g, " ")}
                    </span>
                    <span className="text-lg">
                      {i === 0 ? "🥇" : i === 1 ? "🥈" : "🥉"}
                    </span>
                  </div>
                  <p className="text-white font-semibold text-sm mb-1">{action.skill_name}</p>
                  {action.resource_title && (
                    <p className="text-xs text-gray-400 mb-2">{action.resource_title}</p>
                  )}
                  <p className="text-xs text-gray-500 mb-3">{action.reason}</p>
                  {action.resource_url && (
                    <a
                      href={action.resource_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300"
                    >
                      Open resource <ExternalLink size={10} />
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Weekly plan */}
        {data.weekly_plan && (
          <div className="glass rounded-2xl p-6">
            <h2 className="text-lg font-bold text-white mb-4">📅 This Week's Study Plan</h2>
            <div className="bg-gray-800/40 rounded-xl p-4 text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
              {data.weekly_plan}
            </div>
          </div>
        )}
      </div>

      <TutorChat />
    </div>
  );
}
