/**
 * pages/Onboarding.tsx — Highly polished multi-step card wizard UI for PathMind onboarding.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Sparkles, User, Target, BookOpen, Compass, Loader2 } from "lucide-react";
import { api, type DiagnosticQuestion } from "../api";
import { useStore } from "../store/useStore";

type Step = "profile" | "goal" | "experience" | "quiz" | "done";

const EXPERIENCE_OPTIONS = [
  { value: "beginner", label: "🌱 Beginner", desc: "Just starting out. No prior coding or data experience.", color: "hover:border-purple-500" },
  { value: "intermediate", label: "⚡ Intermediate", desc: "Know some Python, SQL, or math. Ready to specialize.", color: "hover:border-blue-500" },
  { value: "advanced", label: "🚀 Advanced", desc: "Professional background. Looking to master deep topics.", color: "hover:border-emerald-500" },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { setLearner, setTargetSkills, setDiagnosticQuestions } = useStore();

  const [step, setStep] = useState<Step>("profile");
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Quiz state
  const [learnerId, setLearnerId] = useState<number | null>(null);
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<{ question_id: string; answer: string }[]>([]);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [textAnswer, setTextAnswer] = useState("");

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setStep("goal");
  };

  const handleGoalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;
    setStep("experience");
  };

  const handleExperienceSubmit = async (expLevel: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await api.onboard({
        name,
        goal_text: goal,
        interests: [],
        experience_level: expLevel,
      });

      setLearnerId(resp.learner_id);
      setLearner(resp.learner_id, name, goal);
      setTargetSkills(resp.target_skills);
      setDiagnosticQuestions(resp.diagnostic_questions);
      setQuestions(resp.diagnostic_questions);

      setStep("quiz");
      setCurrentQ(0);
    } catch (e: any) {
      setError(
        e.message || "Failed to connect to the server. Please verify the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleNextQuestion = async () => {
    const q = questions[currentQ];
    const answer = q.options ? selectedOption : textAnswer;
    if (!answer) return;

    const newAnswers = [...answers, { question_id: q.question_id, answer }];
    setAnswers(newAnswers);
    setSelectedOption(null);
    setTextAnswer("");

    if (currentQ + 1 < questions.length) {
      setCurrentQ(currentQ + 1);
    } else {
      setLoading(true);
      setError(null);
      try {
        // Submit Quiz
        await api.diagnosticQuiz({
          learner_id: learnerId!,
          answers: newAnswers,
        });

        // Generate Path
        const pathResp = await api.generatePath(learnerId!);
        useStore.getState().setPathNodes(pathResp.nodes);

        setStep("done");
        setTimeout(() => navigate("/tree"), 2000);
      } catch (e: any) {
        setError(e.message || "An error occurred during path calibration.");
      } finally {
        setLoading(false);
      }
    }
  };

  const currentQuestion = questions[currentQ];

  return (
    <div className="min-h-screen grid-bg flex flex-col justify-between py-12 px-4 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-950/80 border border-brand-800 text-xs font-semibold text-brand-300 mb-4 animate-pulse-slow">
          <Sparkles size={12} />
          <span>PROTOTYPE ENGINE</span>
        </div>
        <h1 className="text-5xl font-black tracking-tight text-white sm:text-6xl">
          Path<span className="text-brand-500">Mind</span>
        </h1>
        <p className="mt-2 text-sm text-gray-400">
          AI-Powered Knowledge Graph Roadmap Generator
        </p>
      </div>

      {/* Main Wizard Card */}
      <div className="w-full max-w-xl mx-auto my-auto mt-8">
        <div className="bg-gray-900/90 border border-gray-800 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
          {/* Decorative elements */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/10 rounded-full blur-2xl -mr-16 -mt-16" />
          <div className="absolute bottom-0 left-0 w-32 h-32 bg-purple-500/10 rounded-full blur-2xl -ml-16 -mb-16" />

          {/* Stepper indicators */}
          {step !== "done" && (
            <div className="flex items-center justify-between mb-8 pb-4 border-b border-gray-800/80">
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-semibold transition-all ${
                  step === "profile" ? "bg-brand-500 text-white shadow-lg" : "bg-gray-800 text-gray-400"
                }`}>
                  <User size={14} />
                </div>
                <span className="text-xs font-semibold text-gray-400 hidden sm:inline">Profile</span>
              </div>
              <div className="flex-1 h-0.5 bg-gray-800 mx-2" />
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-semibold transition-all ${
                  step === "goal" ? "bg-brand-500 text-white shadow-lg" : "bg-gray-800 text-gray-400"
                }`}>
                  <Target size={14} />
                </div>
                <span className="text-xs font-semibold text-gray-400 hidden sm:inline">Goal</span>
              </div>
              <div className="flex-1 h-0.5 bg-gray-800 mx-2" />
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-semibold transition-all ${
                  step === "experience" ? "bg-brand-500 text-white shadow-lg" : "bg-gray-800 text-gray-400"
                }`}>
                  <Compass size={14} />
                </div>
                <span className="text-xs font-semibold text-gray-400 hidden sm:inline">Skills</span>
              </div>
              <div className="flex-1 h-0.5 bg-gray-800 mx-2" />
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-semibold transition-all ${
                  step === "quiz" ? "bg-brand-500 text-white shadow-lg" : "bg-gray-800 text-gray-400"
                }`}>
                  <BookOpen size={14} />
                </div>
                <span className="text-xs font-semibold text-gray-400 hidden sm:inline">Quiz</span>
              </div>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 rounded-2xl bg-red-950/50 border border-red-800/80 text-sm text-red-300">
              {error}
            </div>
          )}

          {/* Form Step: Profile */}
          {step === "profile" && (
            <form onSubmit={handleProfileSubmit} className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">Let's start with your name</h2>
                <p className="text-sm text-gray-400">To personalize your Roadmap experience.</p>
              </div>
              <div>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full bg-gray-800/50 border border-gray-700 focus:border-brand-500 focus:outline-none rounded-2xl px-4 py-3.5 text-white placeholder-gray-500 transition-colors"
                />
              </div>
              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2">
                Continue <ArrowRight size={16} />
              </button>
            </form>
          )}

          {/* Form Step: Goal */}
          {step === "goal" && (
            <form onSubmit={handleGoalSubmit} className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">What is your learning goal?</h2>
                <p className="text-sm text-gray-400">Explain what you want to achieve or build in plain English.</p>
              </div>
              <div>
                <textarea
                  required
                  rows={4}
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder='e.g., "I want to become a machine learning engineer in 6 months. I need a path that covers statistics, scikit-learn, deep learning, and deployment. I already know basic programming."'
                  className="w-full bg-gray-800/50 border border-gray-700 focus:border-brand-500 focus:outline-none rounded-2xl p-4 text-white placeholder-gray-500 transition-colors resize-none text-sm leading-relaxed"
                />
              </div>
              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2">
                Analyze Goal <ArrowRight size={16} />
              </button>
            </form>
          )}

          {/* Form Step: Experience */}
          {step === "experience" && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">Select your experience level</h2>
                <p className="text-sm text-gray-400">This helps align the difficulty level of initial materials.</p>
              </div>
              {loading ? (
                <div className="flex flex-col items-center justify-center py-12 gap-3">
                  <Loader2 size={32} className="animate-spin text-brand-500" />
                  <p className="text-sm text-gray-400">Analyzing goal with Groq LLM...</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {EXPERIENCE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => handleExperienceSubmit(opt.value)}
                      className={`w-full text-left p-4 rounded-2xl border border-gray-800 bg-gray-850 hover:bg-gray-800/80 transition-all flex flex-col gap-1 ${opt.color}`}
                    >
                      <span className="text-sm font-bold text-white">{opt.label}</span>
                      <span className="text-xs text-gray-400 leading-normal">{opt.desc}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Form Step: Quiz */}
          {step === "quiz" && currentQuestion && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white">Diagnostic Calibration</h2>
                  <p className="text-xs text-gray-400 mt-0.5">Area: <span className="text-brand-400 font-semibold">{currentQuestion.skill_area}</span></p>
                </div>
                <span className="text-xs bg-brand-950 text-brand-300 px-2.5 py-1 rounded-full border border-brand-800">
                  {currentQ + 1} of {questions.length}
                </span>
              </div>

              <div className="bg-gray-850/50 rounded-2xl p-4 border border-gray-800 text-sm leading-relaxed text-gray-200">
                {currentQuestion.question_text}
              </div>

              {loading ? (
                <div className="flex flex-col items-center justify-center py-8 gap-3">
                  <Loader2 size={24} className="animate-spin text-brand-500" />
                  <p className="text-xs text-gray-400">Calibrating skill path...</p>
                </div>
              ) : currentQuestion.options ? (
                <div className="space-y-2">
                  {currentQuestion.options.map((opt) => (
                    <button
                      key={opt}
                      onClick={() => setSelectedOption(opt)}
                      className={`w-full text-left px-4 py-3 rounded-xl border text-xs transition-all ${
                        selectedOption === opt
                          ? "bg-brand-600 border-brand-400 text-white font-semibold"
                          : "bg-gray-800/50 border-gray-700 text-gray-300 hover:bg-gray-800"
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                  <button
                    onClick={handleNextQuestion}
                    disabled={!selectedOption}
                    className="btn-primary w-full mt-4 flex items-center justify-center gap-2 disabled:opacity-40"
                  >
                    {currentQ + 1 === questions.length ? "Finish & Generate Path" : "Next Question"}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <input
                    type="text"
                    value={textAnswer}
                    onChange={(e) => setTextAnswer(e.target.value)}
                    placeholder="Type your response here..."
                    className="w-full bg-gray-800/50 border border-gray-700 focus:border-brand-500 focus:outline-none rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500"
                  />
                  <button
                    onClick={handleNextQuestion}
                    disabled={!textAnswer.trim()}
                    className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-40"
                  >
                    {currentQ + 1 === questions.length ? "Finish & Generate Path" : "Next Question"}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Form Step: Done */}
          {step === "done" && (
            <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-emerald-950 border border-emerald-800 flex items-center justify-center text-3xl animate-bounce">
                🎉
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">Roadmap Built Successfully!</h2>
                <p className="text-sm text-gray-400 mt-1">Directing you to your interactive RPG Skill Tree...</p>
              </div>
              <Loader2 size={24} className="animate-spin text-brand-500" />
            </div>
          )}
        </div>
      </div>

      {/* Footer copyright */}
      <div className="text-center text-xs text-gray-600">
        PathMind © {new Date().getFullYear()} · Optimized with Groq Llama 3
      </div>
    </div>
  );
}
