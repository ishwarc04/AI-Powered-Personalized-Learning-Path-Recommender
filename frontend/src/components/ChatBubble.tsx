/**
 * components/ChatBubble.tsx — Chat bubble for onboarding and tutor chat.
 */

interface ChatBubbleProps {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
}

export default function ChatBubble({ role, content, timestamp }: ChatBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-sm mr-2 mt-1 flex-shrink-0">
          🤖
        </div>
      )}
      <div
        className={`
          max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
          ${isUser
            ? "bubble-user bg-brand-600 text-white rounded-tr-sm"
            : "bubble-ai bg-gray-800 text-gray-100 border border-gray-700 rounded-tl-sm"
          }
        `}
      >
        <p className="whitespace-pre-wrap">{content}</p>
        {timestamp && (
          <p className={`text-[10px] mt-1 ${isUser ? "text-brand-200" : "text-gray-500"}`}>
            {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </p>
        )}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-sm ml-2 mt-1 flex-shrink-0">
          👤
        </div>
      )}
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3">
      <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-sm mr-2">
        🤖
      </div>
      <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1 items-center">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  );
}
