'use client';

import type { Candidate } from "@/types/interview";

interface CandidateCardProps {
  candidate: Candidate;
  selected: boolean;
  onSelect: () => void;
}

export function CandidateCard({ candidate, selected, onSelect }: CandidateCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`group rounded-3xl border p-6 text-left transition-all duration-200 hover:-translate-y-1 hover:border-cyan-400/50 hover:shadow-2xl ${
        selected
          ? "border-cyan-400/70 bg-cyan-500/10 shadow-lg shadow-cyan-500/10"
          : "border-white/10 bg-slate-900/60"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-white">{candidate.name}</h3>
          <p className="mt-1 text-sm text-cyan-200">{candidate.jobRole}</p>
        </div>
        <span className="rounded-full border border-cyan-400/30 bg-cyan-500/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-cyan-200">
          {candidate.status}
        </span>
      </div>

      <div className="mt-6 space-y-2 text-sm text-slate-300">
        <p>
          <span className="font-medium text-slate-200">Experience:</span> {candidate.yearsExperience} years
        </p>
        <p>
          <span className="font-medium text-slate-200">Education:</span> {candidate.education}
        </p>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <span className={`text-sm ${selected ? "text-emerald-300" : "text-slate-400"}`}>
          {selected ? "Selected ✓" : "Ready for interview"}
        </span>
        <span className="rounded-full bg-white/10 px-3 py-1 text-sm font-medium text-white transition group-hover:bg-cyan-500/20">
          {selected ? "Selected" : "Select"}
        </span>
      </div>
    </button>
  );
}
