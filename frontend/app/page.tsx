'use client';

import { useEffect, useRef, useState } from "react";
import { CandidateCard } from "@/components/CandidateCard";
import { CompletionScreen } from "@/components/CompletionScreen";
import { InterviewSidebar } from "@/components/InterviewSidebar";
import { MessageBubble } from "@/components/MessageBubble";
import type { Candidate, Feedback, InterviewMessage, InterviewResponse } from "@/types/interview";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function buildApiUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

function createSessionId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function isAcknowledgementOnlyMessage(message: string) {
  const normalized = message.trim().toLowerCase();
  if (!normalized) {
    return false;
  }

  const acknowledgementPhrases = [
    "yes",
    "okay",
    "ok",
    "sure",
    "go ahead",
    "go on",
    "proceed",
    "continue",
    "start",
    "begin",
    "i'm ready",
    "im ready",
    "i am ready",
    "ready",
    "sounds good",
    "let's continue",
    "lets continue",
    "please continue",
  ];

  return acknowledgementPhrases.includes(normalized) || normalized.split(/\s+/).length <= 4 && acknowledgementPhrases.some((phrase) => normalized.includes(phrase));
}

export default function Home() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loadingCandidates, setLoadingCandidates] = useState(true);
  const [candidateError, setCandidateError] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isInterviewActive, setIsInterviewActive] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [isInterviewComplete, setIsInterviewComplete] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Select a candidate to begin");
  const [apiError, setApiError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const selectedCandidateRef = useRef<HTMLDivElement>(null);
  const latestRequestRef = useRef(0);

  useEffect(() => {
    let isMounted = true;

    const loadCandidates = async () => {
      try {
        setLoadingCandidates(true);
        setCandidateError(null);
        const response = await fetch(buildApiUrl("/api/candidates"));

        if (!response.ok) {
          throw new Error("Unable to load candidates.");
        }

        const data = (await response.json()) as { candidates?: Candidate[] };
        if (isMounted) {
          setCandidates(data.candidates ?? []);
        }
      } catch {
        if (isMounted) {
          setCandidateError("Unable to load candidates. Please make sure the backend is running.");
        }
      } finally {
        if (isMounted) {
          setLoadingCandidates(false);
        }
      }
    };

    void loadCandidates();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    if (selectedCandidate && !isInterviewActive) {
      selectedCandidateRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [selectedCandidate, isInterviewActive]);

  async function startInterview(candidate: Candidate) {
    setSelectedCandidate(candidate);
    setMessages([]);
    setFeedback(null);
    setIsInterviewComplete(false);
    setIsInterviewActive(true);
    setApiError(null);
    setInput("");
    setStatusMessage("Preparing your AI interview...");
    setIsLoading(true);

    const newSessionId = createSessionId();
    setSessionId(newSessionId);
    const requestId = ++latestRequestRef.current;

    try {
      const response = await fetch(buildApiUrl("/api/interview"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sessionId: newSessionId,
          candidate: {
            id: candidate.id,
            name: candidate.name,
            role: candidate.jobRole,
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Unable to start the interview.");
      }

      if (requestId !== latestRequestRef.current) {
        return;
      }

      const data = (await response.json()) as InterviewResponse;
      const firstMessage: InterviewMessage = {
        id: createSessionId(),
        role: "assistant",
        content: data.reply,
      };

      setMessages([firstMessage]);
      setStatusMessage("Interview started");

      if (data.done) {
        setIsInterviewComplete(true);
        setFeedback(data.feedback ?? null);
        setStatusMessage("Interview complete");
      }
    } catch {
      setApiError("Something went wrong while connecting to the AI interviewer.");
      setStatusMessage("Ready to retry");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSendAnswer() {
    if (!input.trim() || isLoading || isInterviewComplete || !sessionId) {
      return;
    }

    const candidateAnswer = input.trim();
    const candidateMessage: InterviewMessage = {
      id: createSessionId(),
      role: "candidate",
      content: candidateAnswer,
    };

    setMessages((prev) => [...prev, candidateMessage]);
    setInput("");
    setIsLoading(true);
    setApiError(null);
    setStatusMessage("AI Interviewer is thinking...");
    const requestId = ++latestRequestRef.current;

    try {
      const response = await fetch(buildApiUrl("/api/interview"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sessionId,
          message: candidateAnswer,
        }),
      });

      if (!response.ok) {
        throw new Error("Interview request failed.");
      }

      if (requestId !== latestRequestRef.current) {
        return;
      }

      const data = (await response.json()) as InterviewResponse;
      const shouldSuppressAssistantReply = isAcknowledgementOnlyMessage(candidateAnswer) && !data.done;

      if (!shouldSuppressAssistantReply) {
        const assistantMessage: InterviewMessage = {
          id: createSessionId(),
          role: "assistant",
          content: data.reply,
        };

        setMessages((prev) => [...prev, assistantMessage]);
      }

      if (data.done) {
        setIsInterviewComplete(true);
        setFeedback(data.feedback ?? null);
        setStatusMessage("Interview complete");
      } else {
        setStatusMessage("Interview in progress");
      }
    } catch {
      setApiError("Something went wrong while connecting to the AI interviewer.");
      setStatusMessage("Ready to retry");
    } finally {
      setIsLoading(false);
    }
  }

  function resetInterview() {
    setSelectedCandidate(null);
    setMessages([]);
    setInput("");
    setFeedback(null);
    setIsInterviewComplete(false);
    setIsInterviewActive(false);
    setSessionId(null);
    setApiError(null);
    setStatusMessage("Select a candidate to begin");
  }

  const questionCount = messages.filter((message) => message.role === "assistant").length;
  const progress = isInterviewComplete ? 100 : Math.min(100, Math.max(16, questionCount * 12));

  if (!isInterviewActive) {
    return (
      <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),_transparent_35%),linear-gradient(135deg,_#020617_0%,_#0f172a_45%,_#111827_100%)] px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-6">
          <section className="rounded-[36px] border border-white/10 bg-slate-950/70 p-6 shadow-2xl shadow-black/30 backdrop-blur md:p-8 lg:p-10">
            <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
              <div className="space-y-6">
                <div className="inline-flex items-center rounded-full border border-cyan-400/30 bg-cyan-500/10 px-3 py-1 text-sm font-medium text-cyan-200">
                  AI-Powered Interview Preparation
                </div>
                <div className="space-y-4">
                  <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                    GNANEX AI
                  </h1>
                  <p className="max-w-2xl text-lg leading-8 text-slate-300">
                    Practice a realistic technical interview with an adaptive AI interviewer that understands your role, learning path, and curriculum progress.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
                    <span className="font-semibold text-white">31-day AI Cohort</span>
                    <div className="mt-1">RAG • MCP • Agents • Deployment</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
                    <span className="font-semibold text-white">Adaptive follow-ups</span>
                    <div className="mt-1">Role-specific interview flow</div>
                  </div>
                </div>
              </div>

              <div className="rounded-[30px] border border-white/10 bg-gradient-to-br from-slate-900/90 to-slate-800/90 p-6">
                <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">Candidate selection</p>
                <h2 className="mt-3 text-2xl font-semibold text-white">Choose a profile to begin</h2>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  The interview experience adapts to the candidate profile, experience level, and completed curriculum topics.
                </p>

                {selectedCandidate ? (
                  <div ref={selectedCandidateRef} className="mt-6 rounded-2xl border border-cyan-400/20 bg-cyan-500/10 p-4">
                    <p className="text-sm text-emerald-200">Selected ✓</p>
                    <p className="mt-2 text-lg font-semibold text-white">{selectedCandidate.name}</p>
                    <p className="mt-2 text-sm text-slate-200">
                      Candidate selected. Scroll down and press start to begin the AI interview.
                    </p>
                    <button
                      type="button"
                      onClick={() => void startInterview(selectedCandidate)}
                      className="mt-4 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-3 font-medium text-white transition hover:opacity-90"
                    >
                      Start Interview
                    </button>
                  </div>
                ) : null}
              </div>
            </div>

            <div className="mt-8">
              {loadingCandidates ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={index} className="h-40 animate-pulse rounded-3xl border border-white/10 bg-white/5" />
                  ))}
                </div>
              ) : null}

              {candidateError ? (
                <div className="rounded-3xl border border-red-500/30 bg-red-500/10 p-6 text-red-200">
                  {candidateError}
                </div>
              ) : null}

              {!loadingCandidates && !candidateError ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {candidates.map((candidate) => (
                    <CandidateCard
                      key={candidate.id}
                      candidate={candidate}
                      selected={selectedCandidate?.id === candidate.id}
                      onSelect={() => setSelectedCandidate(candidate)}
                    />
                  ))}
                </div>
              ) : null}
            </div>
          </section>
        </div>
      </main>
    );
  }

  if (!selectedCandidate) {
    return (
      <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),_transparent_35%),linear-gradient(135deg,_#020617_0%,_#0f172a_45%,_#111827_100%)] px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-6">
          <section className="rounded-[36px] border border-white/10 bg-slate-950/70 p-8 shadow-2xl shadow-black/30 backdrop-blur">
            <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">Interview ready</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Pick a candidate to continue</h2>
            <p className="mt-3 max-w-2xl text-slate-300">
              Choose a profile from the landing screen and start the interview experience.
            </p>
            <button
              type="button"
              onClick={() => setIsInterviewActive(false)}
              className="mt-6 rounded-full border border-white/10 px-5 py-3 text-sm font-medium text-slate-300 transition hover:bg-white/10"
            >
              Back to candidates
            </button>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),_transparent_35%),linear-gradient(135deg,_#020617_0%,_#0f172a_45%,_#111827_100%)] px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <section className="flex flex-col gap-6 xl:flex-row xl:items-start xl:gap-8">
          <InterviewSidebar
            candidate={selectedCandidate}
            progress={progress}
            questionCount={questionCount}
            status={isInterviewComplete ? "Completed" : isLoading ? "Thinking" : "In progress"}
          />

          <div className="flex-1 rounded-[36px] border border-white/10 bg-slate-950/70 p-4 shadow-2xl shadow-black/30 backdrop-blur sm:p-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 p-4">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">AI Interviewer</p>
                <h2 className="mt-1 text-xl font-semibold text-white">{selectedCandidate.name}</h2>
              </div>
              <div className="flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-2 text-sm text-cyan-100">
                <span className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
                {statusMessage}
              </div>
            </div>

            {apiError ? (
              <div className="mb-4 rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
                {apiError}
              </div>
            ) : null}

            {!isInterviewComplete ? (
              <div className="max-h-[640px] space-y-4 overflow-y-auto rounded-[28px] border border-white/10 bg-slate-900/70 p-4 sm:p-6">
                {messages.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-cyan-400/30 bg-cyan-500/10 p-4 text-sm text-cyan-100">
                    Your interview will begin with an adaptive question tailored to {selectedCandidate.name}.
                  </div>
                ) : null}

                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}

                {isLoading ? (
                  <div className="flex justify-start">
                    <div className="rounded-2xl border border-cyan-400/20 bg-slate-900/80 px-4 py-3 text-sm text-slate-200">
                      AI Interviewer is thinking...
                    </div>
                  </div>
                ) : null}

                <div ref={messagesEndRef} />
              </div>
            ) : (
              <CompletionScreen candidate={selectedCandidate} feedback={feedback} onRestart={resetInterview} />
            )}

            {!isInterviewComplete ? (
              <div className="mt-4 rounded-[24px] border border-white/10 bg-slate-900/70 p-4">
                <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="answer">
                  Your response
                </label>
                <textarea
                  id="answer"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  rows={4}
                  placeholder="Share your technical answer, reasoning, and tradeoffs..."
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 outline-none ring-0 transition focus:border-cyan-400/40"
                  disabled={isLoading}
                />
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm text-slate-400">
                    The agent will adapt based on your answer and maintain context across the interview.
                  </p>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={resetInterview}
                      className="rounded-full border border-white/10 px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-white/10"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleSendAnswer()}
                      disabled={!input.trim() || isLoading}
                      className="rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-2.5 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isLoading ? "Sending..." : "Send Answer"}
                    </button>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}
