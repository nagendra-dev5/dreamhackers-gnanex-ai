'use client';

import type { Candidate } from "@/types/interview";

interface InterviewSidebarProps {
  candidate: Candidate | null;
  progress: number;
  questionCount: number;
  status: string;
}

export function InterviewSidebar({ candidate, progress, questionCount, status }: InterviewSidebarProps) {
  return (
    <aside className="w-full rounded-[28px] border border-white/10 bg-slate-950/70 p-6 shadow-2xl shadow-black/20 backdrop-blur xl:w-80 xl:sticky xl:top-6 xl:self-start">
      <div className="space-y-8">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">GNANEX AI</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Interview Focus</h2>
        </div>

        <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 p-4">
          <p className="text-sm text-cyan-100">Candidate</p>
          <p className="mt-1 text-lg font-semibold text-white">{candidate?.name ?? "Preparing"}</p>
          <p className="mt-1 text-sm text-slate-300">{candidate?.jobRole ?? "Select a profile"}</p>
        </div>

        <div className="space-y-3 rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Status</span>
            <span className="font-medium text-white">{status}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Questions</span>
            <span className="font-medium text-white">{questionCount}</span>
          </div>
          <div className="mt-4">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="text-slate-400">Progress</span>
              <span className="text-white">{progress}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-800">
              <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
