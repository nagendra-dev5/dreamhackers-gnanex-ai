from __future__ import annotations
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class CandidateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[List[str]] = None

    model_config = {
        "extra": "allow",
    }


class InterviewTurn(BaseModel):
    question: str
    answer: Optional[str] = None
    evaluation: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    depth_action: Optional[str] = None


class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[CandidateProfile] = None
    message: Optional[str] = None

    @model_validator(mode="after")
    def validate_request(cls, values):
        session_id = values.sessionId
        candidate = values.candidate
        message = values.message

        if not session_id:
            raise ValueError("sessionId is required")

        if candidate is None and (message is None or not message.strip()):
            raise ValueError("Either candidate profile or a message is required")

        if candidate is not None and message is not None:
            raise ValueError("Provide candidate profile only on the first request or message on subsequent requests")

        return values


class Feedback(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]
    overall_score: Optional[int] = None
    topics_assessed: Optional[List[str]] = None
    question_analysis: Optional[List[Dict[str, str]]] = None
    areas_for_improvement: Optional[List[str]] = None
    skipped_questions: Optional[List[str]] = None


class InterviewResponse(BaseModel):
    reply: str
    done: bool = False
    feedback: Optional[Feedback] = None
    question_count: Optional[int] = None
    substantive_turn_count: Optional[int] = None


class SessionState(BaseModel):
    session_id: str
    candidate: CandidateProfile
    history: List[str] = Field(default_factory=list)
    asked_questions: List[str] = Field(default_factory=list)
    evaluations: List[str] = Field(default_factory=list)
    dialogue: List[Dict[str, str]] = Field(default_factory=list)
    turns: List[InterviewTurn] = Field(default_factory=list)
    current_question: int = 0
    warmup_turns_used: int = 0
    technical_question_count: int = 0
    done: bool = False


class SessionStore:
    _sessions: Dict[str, SessionState] = {}

    @classmethod
    def get(cls, session_id: str) -> Optional[SessionState]:
        return cls._sessions.get(session_id)

    @classmethod
    def create(cls, session_id: str, candidate: CandidateProfile) -> SessionState:
        session = SessionState(session_id=session_id, candidate=candidate)
        cls._sessions[session_id] = session
        return session

    @classmethod
    def update(cls, session: SessionState) -> None:
        cls._sessions[session.session_id] = session

    @classmethod
    def all_sessions(cls) -> Dict[str, SessionState]:
        return dict(cls._sessions)
