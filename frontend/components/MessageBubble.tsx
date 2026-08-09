'use client';

import type { InterviewMessage } from "@/types/interview";

interface MessageBubbleProps {
  message: InterviewMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div className={`flex ${isAssistant ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[85%] rounded-2xl border px-4 py-3 shadow-lg ${
          isAssistant
            ? "border-cyan-400/20 bg-slate-900/80 text-slate-100"
            : "border-cyan-500/30 bg-gradient-to-br from-cyan-500 to-blue-600 text-white"
        }`}
      >
        <div className="mb-1 text-xs font-semibold uppercase tracking-[0.25em] opacity-70">
          {isAssistant ? "AI Interviewer" : "Candidate"}
        </div>
        <div className="whitespace-pre-wrap text-sm leading-6">{message.content}</div>
      </div>
    </div>
  );
}
