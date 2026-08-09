export interface Candidate {
  id: string;
  name: string;
  jobRole: string;
  yearsExperience: number;
  education: string;
  status: string;
}

export interface QuestionAnalysis {
  question: string;
  answer: string;
  evaluation: string;
  topic: string;
  difficulty: string;
  depth_action: string;
}

export interface Feedback {
  summary: string;
  strengths: string[];
  gaps: string[];
  next: string[];
  overall_score?: number;
  topics_assessed?: string[];
  question_analysis?: QuestionAnalysis[];
  areas_for_improvement?: string[];
  skipped_questions?: string[];
}

export interface InterviewMessage {
  id: string;
  role: "assistant" | "candidate";
  content: string;
}

export interface InterviewResponse {
  reply: string;
  done: boolean;
  feedback?: Feedback | null;
}
