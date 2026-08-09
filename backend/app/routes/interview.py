from fastapi import APIRouter, HTTPException

from backend.app.models.session import InterviewRequest, InterviewResponse, SessionStore
from backend.app.services.gemini import GeminiService
from backend.app.services.data_loader import get_all_candidates, DataLoaderError

router = APIRouter(prefix="/api")
service = GeminiService()


@router.post("/interview", response_model=InterviewResponse)
def interview(request: InterviewRequest) -> InterviewResponse:
    session = SessionStore.get(request.sessionId)

    if session is None:
        if request.candidate is None:
            raise HTTPException(
                status_code=400,
                detail="The first request must include a candidate profile.",
            )

        session = SessionStore.create(request.sessionId, request.candidate)
        try:
            response = service.generate_interview_reply(session, request)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        SessionStore.update(session)
        return response

    if session.done:
        feedback_response = service._build_feedback(session)
        return InterviewResponse(reply="Interview completed.", done=True, feedback=feedback_response)

    if request.candidate is not None:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile may only be provided on the first request.",
        )

    if request.message is None or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="A message is required for subsequent requests.",
        )

    try:
        response = service.generate_interview_reply(session, request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    SessionStore.update(session)
    return response



@router.get("/candidates")
def list_candidates():
    """Return a safe list of candidates for selection (non-sensitive fields only)."""
    try:
        data = get_all_candidates()
    except DataLoaderError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    result = []
    for c in data.get("candidates", []):
        member = c.get("member", {})
        item = {
            "id": member.get("id"),
            "name": member.get("name"),
            "jobRole": member.get("jobRole"),
            "yearsExperience": member.get("yearsExperience"),
            "education": member.get("education"),
            "status": member.get("status"),
        }
        result.append(item)

    return {"candidates": result}
