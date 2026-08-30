/**
 * components/TutorChat.tsx — Docked persistent AI tutor chat panel.
 * Available on every page via the floating button.
 */

import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Loader2 } from "lucide-react";
import { api } from "../api";
import { useStore } from "../store/useStore";
import ChatBubble, { TypingIndicator } from "./ChatBubble";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export default function TutorChat() {
  const learnerId = useStore((s) => s.learnerId);
  const learnerName = useStore((s) => s.learnerName);
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `Hi ${learnerName || "there"}! 👋 I'm your PathMind AI tutor. Ask me anything about your learning path — "why is statistics here?", "what should I do this week?", or anything else!`,
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || !learnerId || loading) return;

    const userMsg: Message = {
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const resp = await api.chat(learnerId, userMsg.content);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: resp.reply, timestamp: resp.timestamp },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, I ran into an error: ${e.message}. Please make sure the backend is running.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!learnerId) return null;

  return (
    <>
      {/* Floating button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-brand-500 hover:bg-brand-400
                     flex items-center justify-center shadow-lg z-40
                     transition-all duration-200 hover:scale-110"
          style={{ boxShadow: "0 0 20px rgba(82,97,234,0.5)" }}
        >
          <MessageCircle size={24} className="text-white" />
        </button>
      )}

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-6 right-6 w-96 h-[520px] glass rounded-2xl border border-gray-700
                        flex flex-col z-50 shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-brand-950/60">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-sm">
                🤖
              </div>
              <div>
                <p className="text-sm font-semibold text-white">PathMind Tutor</p>
                <p className="text-[10px] text-brand-400">Powered by Grok AI</p>
              </div>
            </div>
            <button onClick={() => setOpen(false)} className="text-gray-500 hover:text-white transition-colors">
              <X size={18} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            {messages.map((msg, i) => (
              <ChatBubble
                key={i}
                role={msg.role}
                content={msg.content}
                timestamp={msg.timestamp}
              />
            ))}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-gray-700">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Ask anything about your path..."
                rows={2}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2
                           text-sm text-white placeholder-gray-500 resize-none
                           focus:outline-none focus:border-brand-500 transition-colors"
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="w-10 h-10 bg-brand-500 hover:bg-brand-400 disabled:opacity-40
                           rounded-xl flex items-center justify-center transition-colors self-end"
              >
                {loading ? (
                  <Loader2 size={16} className="text-white animate-spin" />
                ) : (
                  <Send size={16} className="text-white" />
                )}
              </button>
            </div>
            <p className="text-[10px] text-gray-600 mt-1 text-center">Press Enter to send · Shift+Enter for new line</p>
          </div>
        </div>
      )}
    </>
  );
}
