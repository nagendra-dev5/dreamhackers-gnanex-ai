from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.app.models.session import CandidateProfile, SessionState
from backend.app.services.data_loader import get_curriculum

DEFAULT_CURRICULUM: List[Dict[str, Any]] = []


def _format_profile(candidate: CandidateProfile) -> str:
    profile = candidate.model_dump(exclude_none=True)
    lines = []
    for key, value in profile.items():
        if key == "skills" and isinstance(value, list):
            lines.append(f"skills: {', '.join(value)}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _format_curriculum(curriculum: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    # curriculum may be a dict (from curriculum.json) or a simple list
    if isinstance(curriculum, dict):
        # prefer modules then days
        modules = curriculum.get("modules") or []
        for m in modules:
            title = m.get("title") or m.get("name") or f"Module {m.get('n') or ''}"
            days = m.get("days")
            lines.append(f"- {title}: days {days}")
        # also include top-level cohort info if present
        if curriculum.get("cohort"):
            lines.insert(0, f"Cohort: {curriculum.get('cohort')}")
    elif isinstance(curriculum, list):
        for item in curriculum:
            lines.append(f"- {item.get('name')}: {item.get('description')}")
    return "\n".join(lines)


def _format_dialogue(session: SessionState) -> str:
    if not session.dialogue:
        return "No previous questions or answers."

    lines: List[str] = []
    for turn in session.dialogue:
        role = turn.get("role", "assistant")
        content = turn.get("content", "")
        prefix = "Q:" if role == "assistant" else "A:"
        lines.append(f"{prefix} {content}")
    return "\n".join(lines)


def build_interview_prompt(
    candidate: CandidateProfile,
    curriculum: Optional[List[Dict[str, Any]]],
    session: SessionState,
    latest_answer: Optional[str] = None,
    first_request: bool = False,
) -> str:
    curriculum = curriculum or DEFAULT_CURRICULUM
    warmup_stage = first_request or (
        session.warmup_turns_used < 2 and session.technical_question_count < 1
    )

    prompt_lines: List[str] = [
        "You are GNANEX, an adaptive technical interview assistant powered by Gemini.",
        "Use the candidate profile and curriculum topics to choose relevant interview subjects dynamically.",
        "Do not select from a fixed question list.",
        "Keep the conversation natural, technical, and focused on skills that match the candidate's role and experience.",
        "",
        "Candidate profile:",
        _format_profile(candidate),
        "",
        "Curriculum topics:",
        _format_curriculum(curriculum),
        "",
        "Interview state:",
        f"Questions already asked: {len(session.asked_questions)}",
        f"Previous dialogue:\n{_format_dialogue(session)}",
    ]

    if latest_answer is not None:
        prompt_lines.extend(
            [
                "",
                "Latest candidate answer:",
                latest_answer,
            ]
        )
    else:
        prompt_lines.extend(
            [
                "",
                "Latest candidate answer:",
                "N/A. This is the first interview turn.",
            ]
        )

    prompt_lines.extend(
        [
            "",
            "Rules:",
            "1. If this is the opening turn, start with a brief, personalized warm-up that feels conversational and grounded in the candidate profile. Do not open with a hard technical question.",
            "2. If the interview is still in the warm-up phase, keep the exchange short and human-like, then transition naturally into a technical question after 1-2 warm-up turns.",
            "3. Once the warm-up phase is complete, ask technically relevant questions based on the candidate profile and curriculum.",
            "4. On follow-up turns, evaluate the latest answer and choose whether to deepen, clarify, or move on.",
            "5. If the answer shows strong understanding, ask a deeper or harder follow-up on the same topic.",
            "6. If the answer shows weak understanding, ask a clarification or remedial question before moving on.",
            "7. Avoid repeating any questions that were already asked.",
            "8. Only return valid JSON. Do not include any explanation outside the JSON object.",
            "9. Use the exact keys: reply, evaluation, topic, difficulty, depth_action, done.",
            "10. reply must be the next interview question, or a clear closing message when done=true.",
            "11. evaluation must briefly assess the latest answer or state 'Profile reviewed.' for the first question.",
            "12. topic should identify the skill or subject being assessed; for warm-up turns use a natural topic such as cohort journey or project experience.",
            "13. difficulty must be one of easy, medium, or hard.",
            "14. depth_action must be one of deeper, clarify, or move_on.",
            "15. done must be false until the interview is complete.",
            "",
            "Reply in JSON exactly like this example:",
            "{\n  \"reply\": \"...\",\n  \"evaluation\": \"...\",\n  \"topic\": \"...\",\n  \"difficulty\": \"easy|medium|hard\",\n  \"depth_action\": \"deeper|clarify|move_on\",\n  \"done\": false\n}",
        ]
    )

    if warmup_stage:
        prompt_lines.extend(
            [
                "",
                "Warm-up mode:",
                "- Start by acknowledging the candidate's background and making the interview feel personal.",
                "- Keep the first 1-2 turns conversational, using the candidate's role, completed missions, projects, or learning signals.",
                "- Then transition naturally to a technical topic tied to the candidate's experience.",
            ]
        )
    else:
        prompt_lines.extend(
            [
                "",
                "Technical assessment mode:",
                "- Build on the latest answer and ask a follow-up or new technical question that is grounded in the conversation.",
                "- Move across curriculum topics over time and avoid repeating questions.",
            ]
        )

    return "\n".join(prompt_lines)


def get_default_curriculum() -> List[Dict[str, Any]]:
    try:
        data = get_curriculum()
        return data
    except Exception:
        return DEFAULT_CURRICULUM
