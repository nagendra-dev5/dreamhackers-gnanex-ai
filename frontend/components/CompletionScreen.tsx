'use client';

import type { Candidate, Feedback } from "@/types/interview";

interface CompletionScreenProps {
  candidate: Candidate | null;
  feedback: Feedback | null;
  onRestart: () => void;
}

export function CompletionScreen({ candidate, feedback, onRestart }: CompletionScreenProps) {
  return (
    <div className="rounded-[32px] border border-cyan-400/20 bg-gradient-to-br from-slate-900/90 to-slate-950/90 p-8 shadow-2xl shadow-cyan-500/10">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">Interview complete</p>
          <h3 className="mt-2 text-3xl font-semibold text-white">You completed a strong technical interview.</h3>
          <p className="mt-3 max-w-2xl text-slate-300">
            {candidate?.name ?? "The candidate"} is now wrapped with a structured AI review and next-step guidance.
          </p>
        </div>
        <button
          type="button"
          onClick={onRestart}
          className="rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-3 font-medium text-white transition hover:opacity-90"
        >
          Start New Interview
        </button>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <p className="text-sm text-slate-400">Candidate</p>
          <p className="mt-2 text-lg font-semibold text-white">{candidate?.name ?? "N/A"}</p>
          <p className="mt-1 text-sm text-slate-300">{candidate?.jobRole ?? "N/A"}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <p className="text-sm text-slate-400">Assessment</p>
          <p className="mt-2 text-lg font-semibold text-white">Adaptive technical review</p>
          <p className="mt-1 text-sm text-slate-300">Built from the final interview session.</p>
        </div>
        {feedback?.overall_score !== undefined ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <p className="text-sm text-slate-400">Score</p>
            <p className="mt-2 text-3xl font-semibold text-white">{feedback.overall_score}%</p>
            <p className="mt-1 text-sm text-slate-300">AI confidence estimate</p>
          </div>
        ) : null}
        {feedback?.topics_assessed ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <p className="text-sm text-slate-400">Topics</p>
            <p className="mt-2 text-lg font-semibold text-white">{feedback.topics_assessed.length}</p>
            <p className="mt-1 text-sm text-slate-300">Topics assessed in interview</p>
          </div>
        ) : null}
      </div>

      {feedback ? (
        <div className="mt-8 space-y-4 rounded-3xl border border-white/10 bg-slate-950/70 p-6">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">AI feedback</p>
            <p className="mt-2 text-lg text-white">{feedback.summary}</p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm font-semibold text-white">Strengths</p>
              <ul className="mt-2 space-y-2 text-sm text-slate-300">
                {feedback.strengths.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Gaps</p>
              <ul className="mt-2 space-y-2 text-sm text-slate-300">
                {feedback.gaps.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Next steps</p>
              <ul className="mt-2 space-y-2 text-sm text-slate-300">
                {feedback.next.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            </div>
          </div>

          {feedback.question_analysis?.length ? (
            <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-4">
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300">Question review</p>
              <div className="mt-4 space-y-3">
                {feedback.question_analysis.slice(0, 3).map((turn, index) => (
                  <div key={`${turn.question}-${index}`} className="rounded-2xl border border-white/10 bg-slate-950/80 p-4">
                    <p className="text-sm font-semibold text-white">Q: {turn.question}</p>
                    <p className="mt-2 text-sm text-slate-300">A: {turn.answer || "No response captured."}</p>
                    <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-500">
                      Topic: {turn.topic || "unknown"} • {turn.difficulty || "unknown"} • {turn.depth_action || "unknown"}
                    </p>
                    {turn.evaluation ? (
                      <p className="mt-2 text-sm text-slate-300">Evaluation: {turn.evaluation}</p>
                    ) : null}
                  </div>
                ))}
                {feedback.question_analysis.length > 3 ? (
                  <p className="text-sm text-slate-400">Plus {feedback.question_analysis.length - 3} more question review entries.</p>
                ) : null}
              </div>
            </div>
          ) : null}

          {feedback.skipped_questions?.length ? (
            <div className="rounded-3xl border border-amber-400/20 bg-amber-500/5 p-4">
              <p className="text-sm font-semibold text-amber-200">Skipped questions</p>
              <ul className="mt-2 space-y-2 text-sm text-amber-100">
                {feedback.skipped_questions.map((question) => (
                  <li key={question}>• {question}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
