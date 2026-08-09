import json
import os
import re
import random
from typing import Any, Dict, List, Optional

from google import genai

from backend.app.models.session import (
    CandidateProfile,
    Feedback,
    InterviewRequest,
    InterviewResponse,
    InterviewTurn,
    SessionState,
)
from backend.app.services.data_loader import (
    enrich_candidate_profile,
    get_curriculum,
)
from backend.app.services.gemini_prompt import build_interview_prompt


class GeminiServiceError(Exception):
    pass


class GeminiService:
    MODEL_NAME = "gemini-3.5-flash"
    MAX_TURNS = 10

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_interview_reply(
        self,
        session: SessionState,
        request: InterviewRequest,
    ) -> InterviewResponse:

        if not self.api_key or self.client is None:
            raise GeminiServiceError(
                "Gemini API key is not configured. "
                "Set GEMINI_API_KEY in backend/.env."
            )

        try:
            if request.candidate is not None:
                return self._handle_first_request(session, request)

            return self._handle_follow_up(session, request)

        except Exception as exc:
            raise GeminiServiceError(str(exc)) from exc

    def _make_response(
        self,
        reply: str,
        done: bool,
        session: SessionState,
        feedback: Optional[Feedback] = None,
    ) -> InterviewResponse:
        return InterviewResponse(
            reply=reply,
            done=done,
            feedback=feedback,
            question_count=len(session.asked_questions),
            substantive_turn_count=sum(
                1 for turn in session.turns if turn.answer is not None
            ),
        )

    def _should_use_warmup(
        self,
        session: SessionState,
        first_request: bool = False,
    ) -> bool:
        return first_request or (
            session.warmup_turns_used < 2 and session.technical_question_count < 1
        )

    def _handle_first_request(
        self,
        session: SessionState,
        request: InterviewRequest,
    ) -> InterviewResponse:

        try:
            raw = (
                request.candidate.model_dump()
                if hasattr(request.candidate, "model_dump")
                else dict(request.candidate)
            )
        except Exception:
            raw = {}

        enriched = enrich_candidate_profile(raw)

        flattened: Dict[str, Any] = {}

        member = (
            enriched.get("member")
            if isinstance(enriched.get("member"), dict)
            else None
        )

        if member:
            flattened.update(member)

        if enriched.get("missions"):
            flattened["missions"] = enriched.get("missions")

        if enriched.get("signals"):
            flattened["signals"] = enriched.get("signals")

        try:
            session.candidate = CandidateProfile.model_validate(flattened)
        except Exception:
            session.candidate = request.candidate

        prompt = build_interview_prompt(
            session.candidate,
            get_curriculum(),
            session,
            latest_answer=None,
            first_request=True,
        )

        parsed = self._run_gemini(prompt, session=session, latest_answer=None)

        if self._should_use_warmup(session, first_request=True):
            session.warmup_turns_used += 1
        else:
            session.technical_question_count += 1

        session.current_question += 1

        if parsed["done"]:
            session.done = True
            return self._make_response(
                reply=parsed["reply"],
                done=True,
                session=session,
                feedback=self._build_feedback(session),
            )

        session.asked_questions.append(parsed["reply"])
        session.dialogue.append(
            {
                "role": "assistant",
                "content": parsed["reply"],
            }
        )

        session.turns.append(
            InterviewTurn(
                question=parsed["reply"],
                topic=parsed["topic"],
                difficulty=parsed["difficulty"],
                depth_action=parsed["depth_action"],
            )
        )

        return self._make_response(
            reply=parsed["reply"],
            done=False,
            session=session,
        )

    def _is_non_answer_message(self, message: str) -> bool:
        normalized = message.strip().lower()
        if not normalized:
            return False

        # Valid interview answers that are intentionally short or express uncertainty.
        valid_answer_clues = [
            "i don't know",
            "dont know",
            "do not know",
            "not sure",
            "i would",
            "i'd",
            "would use",
            "it depends",
            "because",
            "pass",
            "skip",
        ]
        if any(clue in normalized for clue in valid_answer_clues):
            return False

        greetings = [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        ]
        if any(
            normalized == greeting
            or normalized.startswith(greeting + " ")
            for greeting in greetings
        ):
            return True

        control_phrases = [
            "start the answer now",
            "yes proceed",
            "okay",
            "ok",
            "sure",
            "continue",
            "go ahead",
            "i am ready",
            "i'm ready",
            "proceed",
            "let's continue",
            "lets continue",
            "ready",
            "go on",
            "sounds good",
            "please continue",
            "start now",
            "begin now",
        ]
        if normalized in control_phrases:
            return True

        short_message = normalized
        if len(short_message.split()) <= 4 and any(
            word in short_message for word in [
                "okay",
                "ok",
                "sure",
                "continue",
                "proceed",
                "ready",
                "yes",
                "go ahead",
                "go on",
            ]
        ):
            return True

        return False

    def _handle_follow_up(
        self,
        session: SessionState,
        request: InterviewRequest,
    ) -> InterviewResponse:

        if session.current_question >= self.MAX_TURNS:
            session.done = True
            return self._make_response(
                reply="The interview is complete. Thank you for your time.",
                done=True,
                session=session,
                feedback=self._build_feedback(session),
            )

        latest_answer = request.message.strip()

        if self._is_non_answer_message(latest_answer):
            return self._make_response(
                reply="Sure — take your time. Please answer the question above when you're ready.",
                done=False,
                session=session,
            )

        session.history.append(latest_answer)

        session.dialogue.append(
            {
                "role": "candidate",
                "content": latest_answer,
            }
        )

        latest_turn = session.turns[-1] if session.turns else None
        if latest_turn:
            latest_turn.answer = latest_answer
        else:
            session.turns.append(
                InterviewTurn(
                    question="Interview answer",
                    answer=latest_answer,
                )
            )

        prompt = build_interview_prompt(
            session.candidate,
            get_curriculum(),
            session,
            latest_answer=latest_answer,
            first_request=False,
        )

        parsed = self._run_gemini(prompt, session=session, latest_answer=latest_answer)

        if self._should_use_warmup(session):
            session.warmup_turns_used += 1
        else:
            session.technical_question_count += 1

        session.evaluations.append(
            parsed.get("evaluation", "")
        )

        if latest_turn:
            latest_turn.evaluation = parsed.get("evaluation", "")
            latest_turn.topic = parsed.get("topic")
            latest_turn.difficulty = parsed.get("difficulty")
            latest_turn.depth_action = parsed.get("depth_action")

        if parsed["done"]:
            session.done = True
            return self._make_response(
                reply=parsed["reply"],
                done=True,
                session=session,
                feedback=self._build_feedback(session),
            )

        if parsed["reply"] not in session.asked_questions:
            session.asked_questions.append(parsed["reply"])

        session.dialogue.append(
            {
                "role": "assistant",
                "content": parsed["reply"],
            }
        )

        session.current_question += 1
        session.turns.append(
            InterviewTurn(
                question=parsed["reply"],
                topic=parsed["topic"],
                difficulty=parsed["difficulty"],
                depth_action=parsed["depth_action"],
            )
        )

        return self._make_response(
            reply=parsed["reply"],
            done=False,
            session=session,
        )

    def _run_gemini(
        self,
        prompt: str,
        session: Optional[SessionState] = None,
        latest_answer: Optional[str] = None,
    ) -> Dict[str, Any]:

        if self.client is None:
            raise GeminiServiceError(
                "Gemini client is not initialized."
            )

        try:
            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=prompt,
            )
        except Exception as exc:
            # If Gemini is temporarily rate-limited / quota-exhausted, return
            # a small, realistic fallback response so the hackathon demo
            # remains functional and the frontend doesn't receive a 502.
            # This fallback is intentionally lightweight and only used when
            # the Gemini free-tier is exhausted (e.g. RESOURCE_EXHAUSTED / 429).
            err_text = str(exc)
            if (
                "RESOURCE_EXHAUSTED" in err_text
                or "429" in err_text
                or "generate_content_free_tier_requests" in err_text
                or "quota" in err_text.lower()
            ):
                # Log a concise server-side message so operators know the
                # fallback was used (keeps frontend from seeing HTTP 502).
                # This log is intentionally small and only intended for
                # transient demo visibility when Gemini quota is exhausted.
                print("[Gemini] Quota exhausted — using interview fallback.")
                return self._fallback_response(
                    prompt,
                    session=session,
                    latest_answer=latest_answer,
                )

            raise GeminiServiceError(
                f"Gemini API request failed: {exc}"
            ) from exc

        raw_text = getattr(response, "text", None)

        if not raw_text:
            raise GeminiServiceError(
                "Gemini returned an empty response."
            )

        raw_text = raw_text.strip()

        parsed = self._parse_json_response(raw_text)

        self._validate_parsed_response(parsed)

        return parsed

    def _fallback_response(
        self,
        prompt: str,
        session: Optional[SessionState] = None,
        latest_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Demo fallback used when Gemini free-tier quota is exhausted (HTTP 429 / RESOURCE_EXHAUSTED).
        This keeps the hackathon interview demo functional by returning a valid, interview-like
        response so the frontend can continue the flow. It is NOT a replacement for Gemini
        and should only be used transiently while quota limits are in effect.
        """

        topics = [
            "system design",
            "scalability",
            "distributed systems",
            "testing",
            "performance",
            "algorithms",
        ]

        def classify_answer(answer: str) -> str:
            normalized = answer.lower().strip()
            if any(phrase in normalized for phrase in [
                "don't know",
                "dont know",
                "do not know",
                "not sure",
                "no idea",
                "unsure",
            ]):
                return "dont_know"

            if any(phrase in normalized for phrase in ["pass", "skip this", "skip that"]):
                return "pass"

            words = normalized.split()
            if len(words) <= 8:
                return "unclear"

            strong_terms = [
                "scalability",
                "latency",
                "throughput",
                "consistency",
                "availability",
                "cache",
                "sharding",
                "replication",
                "fault tolerance",
                "monitoring",
                "tradeoff",
                "benchmark",
                "load",
                "partition",
                "concurrency",
                "pipeline",
                "resilience",
                "error handling",
                "retry",
                "backoff",
                "state",
                "performance",
            ]
            partial_terms = [
                "maybe",
                "could",
                "often",
                "sometimes",
                "usually",
                "some",
                "partial",
                "kind of",
                "sort of",
                "if",
                "depends",
            ]
            weak_terms = [
                "guess",
                "probably",
                "I think",
                "not sure",
                "maybe",
                "could",
                "would",
                "should",
            ]

            strong_matches = sum(1 for term in strong_terms if term in normalized)
            partial_matches = sum(1 for term in partial_terms if term in normalized)
            weak_matches = sum(1 for term in weak_terms if term in normalized)

            if strong_matches >= 2 or (len(words) > 20 and strong_matches >= 1):
                return "strong"

            if partial_matches >= 2 or (strong_matches >= 1 and len(words) >= 12):
                return "partial"

            if weak_matches >= 2:
                return "weak"

            return "partial" if len(words) >= 12 else "unclear"

        def select_next_topic(current_topic: Optional[str]) -> str:
            candidates = [topic for topic in topics if topic != current_topic]
            unseen = [topic for topic in candidates if topic not in {turn.topic for turn in session.turns if turn.topic}] if session else candidates
            if unseen:
                return random.choice(unseen)
            if candidates:
                return random.choice(candidates)
            return random.choice(topics)

        def same_topic_followups(topic: Optional[str]) -> int:
            if topic is None or session is None:
                return 0
            count = 0
            for turn in reversed(session.turns):
                if turn.topic == topic:
                    count += 1
                else:
                    break
            return count

        def build_warmup_question(candidate: Optional[CandidateProfile]) -> Dict[str, Any]:
            name = (candidate.name or "there").split()[0] if candidate and candidate.name else "there"
            role = candidate.role or "your role"
            recent_topics = []
            if candidate and getattr(candidate, "missions", None):
                recent_topics = [
                    mission.get("title")
                    for mission in candidate.missions
                    if isinstance(mission, dict) and mission.get("title")
                ][:3]
            feature = recent_topics[0] if recent_topics else "the cohort"
            return {
                "reply": f"Hi {name}, welcome. Before we get into the technical discussion, I’d love to understand your journey through the AI Cohort a bit better. What part of {feature} has stood out most to you so far?",
                "evaluation": "Warm-up fallback turn to establish rapport and understand the candidate's journey.",
                "topic": "cohort journey",
                "difficulty": "easy",
                "depth_action": "clarify",
                "done": False,
            }

        def build_warmup_followup(candidate: Optional[CandidateProfile], latest_answer: str) -> Dict[str, Any]:
            name = (candidate.name or "there").split()[0] if candidate and candidate.name else "there"
            return {
                "reply": f"Thanks for sharing that, {name}. What did you learn from that experience, and how did it shape the way you approach similar problems now?",
                "evaluation": "Warm-up follow-up fallback to keep the conversation human and contextual.",
                "topic": "cohort journey",
                "difficulty": "easy",
                "depth_action": "clarify",
                "done": False,
            }

        def build_question(topic: str, classification: str, move_on: bool) -> Dict[str, Any]:
            if classification == "initial":
                return {
                    "reply": f"Let's get started with {topic}. How would you approach a typical {topic} problem?",
                    "evaluation": "Initial fallback interview question for the current session.",
                    "topic": topic,
                    "difficulty": "easy",
                    "depth_action": "move_on",
                    "done": False,
                }

            if classification == "strong":
                return {
                    "reply": f"That was a strong answer on {topic}. Can you go deeper and explain how you'd handle the hardest part of that design?",
                    "evaluation": f"Strong answer on {topic}; follow-up requested deeper reasoning.",
                    "topic": topic,
                    "difficulty": "hard" if not move_on else "medium",
                    "depth_action": "deeper" if not move_on else "move_on",
                    "done": False,
                }

            if classification == "partial":
                return {
                    "reply": f"You're on the right track on {topic}. What key detail would you add to complete the reasoning?",
                    "evaluation": f"Partial answer on {topic}; asked for missing detail.",
                    "topic": topic,
                    "difficulty": "medium",
                    "depth_action": "clarify" if not move_on else "move_on",
                    "done": False,
                }

            if classification == "weak":
                return {
                    "reply": f"I want a clearer approach on {topic}. What is the most important thing to get right in this case?",
                    "evaluation": f"Weak answer on {topic}; offered a simpler clarification.",
                    "topic": topic,
                    "difficulty": "easy" if not move_on else "easy",
                    "depth_action": "clarify" if not move_on else "move_on",
                    "done": False,
                }

            if classification == "dont_know":
                return {
                    "reply": f"That's okay. Let's move on from {topic} and try a related topic instead.",
                    "evaluation": f"Candidate chose not to answer on {topic}; moving on.",
                    "topic": topic,
                    "difficulty": "easy",
                    "depth_action": "move_on",
                    "done": False,
                }

            if classification == "pass":
                return {
                    "reply": f"Understood. We'll skip that and continue with another topic related to {topic}.",
                    "evaluation": f"Candidate passed on {topic}; question skipped.",
                    "topic": topic,
                    "difficulty": "easy",
                    "depth_action": "move_on",
                    "done": False,
                }

            return {
                "reply": f"Can you say a bit more about how you'd approach {topic}?",
                "evaluation": f"Unclear answer on {topic}; asked for clarification.",
                "topic": topic,
                "difficulty": "medium",
                "depth_action": "clarify",
                "done": False,
            }

        if session is None:
            return build_warmup_question(None)

        if not session.turns:
            return build_warmup_question(session.candidate)

        if session.warmup_turns_used < 2 and session.technical_question_count < 1:
            if latest_answer is None:
                return build_warmup_question(session.candidate)
            return build_warmup_followup(session.candidate, latest_answer)

        if latest_answer is None or not session.turns:
            topic = topics[0] if not session else select_next_topic(None)
            return build_question(topic, "initial", move_on=True)

        classification = classify_answer(latest_answer)
        current_topic = session.turns[-1].topic or select_next_topic(None)
        followup_count = same_topic_followups(current_topic)

        if classification in {"dont_know", "pass"}:
            next_topic = select_next_topic(current_topic)
            return build_question(next_topic, classification, move_on=True)

        if classification == "unclear":
            if followup_count < 2:
                return build_question(current_topic, "unclear", move_on=False)
            return build_question(select_next_topic(current_topic), "unclear", move_on=True)

        if classification == "strong":
            if followup_count < 2:
                return build_question(current_topic, "strong", move_on=False)
            return build_question(select_next_topic(current_topic), "strong", move_on=True)

        if classification == "partial":
            if followup_count < 2:
                return build_question(current_topic, "partial", move_on=False)
            return build_question(select_next_topic(current_topic), "partial", move_on=True)

        if classification == "weak":
            if followup_count < 1:
                return build_question(current_topic, "weak", move_on=False)
            return build_question(select_next_topic(current_topic), "weak", move_on=True)

        return build_question(select_next_topic(current_topic), "partial", move_on=True)

    def _parse_json_response(
        self,
        text: str,
    ) -> Dict[str, Any]:

        json_text = text

        if not text.startswith("{") or not text.endswith("}"):

            match = re.search(
                r"(\{.*\})",
                text,
                re.S,
            )

            if match:
                json_text = match.group(1)
            else:
                raise GeminiServiceError(
                    "Could not extract JSON from Gemini response."
                )

        try:
            return json.loads(json_text)

        except json.JSONDecodeError as exc:
            raise GeminiServiceError(
                f"Failed to parse Gemini JSON output: {exc.msg}"
            ) from exc

    def _validate_parsed_response(
        self,
        parsed: Dict[str, Any],
    ) -> None:

        required_keys = {
            "reply": str,
            "evaluation": str,
            "topic": str,
            "difficulty": str,
            "depth_action": str,
            "done": bool,
        }

        for key, expected_type in required_keys.items():

            if key not in parsed:
                raise GeminiServiceError(
                    f"Gemini response is missing required field: {key}"
                )

            if not isinstance(
                parsed[key],
                expected_type,
            ):
                raise GeminiServiceError(
                    f"Gemini response field '{key}' "
                    f"must be of type "
                    f"{expected_type.__name__}."
                )

        if parsed["difficulty"] not in {
            "easy",
            "medium",
            "hard",
        }:
            raise GeminiServiceError(
                "Gemini response difficulty must be "
                "one of easy, medium, or hard."
            )

        if parsed["depth_action"] not in {
            "deeper",
            "clarify",
            "move_on",
        }:
            raise GeminiServiceError(
                "Gemini response depth_action must be "
                "one of deeper, clarify, or move_on."
            )

    def _build_feedback(
        self,
        session: SessionState,
    ) -> Feedback:

        strengths: List[str] = []
        gaps: List[str] = []

        combined = " ".join(
            session.evaluations
        ).lower()

        if "strong" in combined or "deep" in combined:
            strengths.append(
                "Strong technical reasoning"
            )

        if "clear" in combined or "structured" in combined:
            strengths.append(
                "Clear communication"
            )

        if (
            "partial" in combined
            or "some gaps" in combined
            or "unclear" in combined
        ):
            gaps.append(
                "Needs more depth on key concepts"
            )

        if (
            "weak" in combined
            or "missing" in combined
            or "incorrect" in combined
        ):
            gaps.append(
                "Clarify core fundamentals before advancing"
            )

        if not strengths:
            strengths = [
                "Relevant domain knowledge",
                "Thoughtful problem-solving",
            ]

        if not gaps:
            gaps = [
                "Explore deeper technical assumptions",
                "Practice articulating design tradeoffs",
            ]

        topics = sorted(
            {
                turn.topic
                for turn in session.turns
                if turn.topic
            }
        )

        analysis: List[Dict[str, str]] = []
        for turn in session.turns:
            analysis.append(
                {
                    "question": turn.question,
                    "answer": turn.answer or "",
                    "evaluation": turn.evaluation or "",
                    "topic": turn.topic or "",
                    "difficulty": turn.difficulty or "",
                    "depth_action": turn.depth_action or "",
                }
            )

        if not strengths and not gaps:
            combined = " ".join(
                filter(None, [turn.evaluation for turn in session.turns])
            ).lower()

            if "strong" in combined or "deep" in combined:
                strengths.append("Strong technical reasoning")

            if "clear" in combined or "structured" in combined:
                strengths.append("Clear communication")

            if (
                "partial" in combined
                or "some gaps" in combined
                or "unclear" in combined
            ):
                gaps.append("Needs more depth on key concepts")

            if (
                "weak" in combined
                or "missing" in combined
                or "incorrect" in combined
            ):
                gaps.append(
                    "Clarify core fundamentals before advancing"
                )

        if not strengths:
            strengths = [
                "Relevant domain knowledge",
                "Thoughtful problem-solving",
            ]

        if not gaps:
            gaps = [
                "Explore deeper technical assumptions",
                "Practice articulating design tradeoffs",
            ]

        skipped_questions = [
            turn.question
            for turn in session.turns
            if turn.answer is None
            or (
                turn.evaluation
                and any(keyword in turn.evaluation.lower() for keyword in [
                    "moved on",
                    "passed",
                    "chose not to answer",
                    "skipped",
                ])
            )
        ]

        strong_count = sum(
            1
            for turn in session.turns
            if turn.evaluation
            and any(word in turn.evaluation.lower() for word in ["strong", "clear", "deep", "excellent", "solid"])
        )
        weak_count = sum(
            1
            for turn in session.turns
            if turn.evaluation
            and any(word in turn.evaluation.lower() for word in ["weak", "partial", "unclear", "missing", "incorrect"])
        )

        score = None
        substantive_answers = [
            turn
            for turn in session.turns
            if turn.answer and len(turn.answer.strip().split()) >= 4
        ]
        if len(substantive_answers) >= 3:
            score = int(
                round(
                    max(0.0, min(1.0, (strong_count - weak_count) / len(substantive_answers)))
                    * 100
                )
            )

        next_steps = [
            "Review the fundamentals of the most relevant curriculum topics.",
            "Practice follow-up questions that require deeper system reasoning.",
        ]

        summary = (
            f"Interview completed with {len(session.turns)} turn(s). "
            f"The candidate demonstrated strengths across {len(topics)} assessed topic(s)."
        )

        return Feedback(
            summary=summary,
            strengths=list(dict.fromkeys(strengths)),
            gaps=list(dict.fromkeys(gaps)),
            next=next_steps,
            overall_score=score,
            topics_assessed=topics or None,
            question_analysis=analysis,
            areas_for_improvement=gaps,
            skipped_questions=skipped_questions or None,
        )
