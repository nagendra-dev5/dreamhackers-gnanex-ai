# GNANEX AI AI Usage Log / Development Prompt History

This document summarizes the actual AI-assisted development work that shaped the GNANEX AI interview agent. It is intended for hackathon review and authenticity, and it reflects the repository state and the development history that was used to build the current application.

## 1. Initial project / architecture

- Goal: establish a full-stack prototype for an AI technical interview agent.
- What was requested from the AI assistant: propose a practical architecture that could support a conversational interview workflow, candidate selection, and structured feedback.
- What was implemented: a FastAPI backend, a Next.js frontend, a candidate-selection workflow, and a data-driven structure for candidate and curriculum content.
- Important decisions: keep the backend focused on interview orchestration and state management, while the frontend handles the chat experience and candidate selection.
- Validation performed: repository structure was created and basic backend/frontend entry points were exercised.

## 2. Backend interview endpoint

- Goal: create the main interview API and expose a simple route for starting and continuing interviews.
- What was requested from the AI assistant: implement an endpoint that accepts a session identifier plus either a candidate profile or a follow-up message.
- What was implemented: the /api/interview route was added to start a new interview or continue an existing session, and the /api/candidates route was added to return candidate metadata for the UI.
- Important decisions: use a session identifier to tie follow-up requests to the same interview state.
- Validation performed: live requests to the endpoint returned interview replies and the expected JSON structure.

## 3. Gemini integration

- Goal: connect the interview flow to Gemini so the agent could generate interview replies.
- What was requested from the AI assistant: wire the backend to an AI generation path that could respond to candidate answers in a realistic interview style.
- What was implemented: a Gemini-backed service was added to generate replies, use candidate context, and keep the conversation moving.
- Important decisions: keep the interviewer prompt contextual and curriculum-aware rather than treating the interaction like a generic chatbot.
- Validation performed: backend requests produced interview-style replies when Gemini was available.

## 4. Session / interview state

- Goal: preserve context across turns instead of treating each request as an isolated interaction.
- What was requested from the AI assistant: add session state that could remember prior questions, answers, evaluations, and conversation flow.
- What was implemented: a session model was created to store dialogue, assessed topics, question history, warm-up usage, technical-question counters, and completion state.
- Important decisions: make the state explicit in the backend so follow-up questions can stay coherent and structured.
- Validation performed: multi-turn request handling was exercised and the state was preserved across the interview flow.

## 5. Structured interview turns

- Goal: make the interview feel more realistic and trackable by storing structured turns.
- What was requested from the AI assistant: represent each interview turn as a structured object that captures the question, answer, evaluation, and topic context.
- What was implemented: interview turn models were added to represent each question/answer pair and to support later feedback generation.
- Important decisions: include topic and difficulty metadata so feedback and transitions can be more meaningful.
- Validation performed: the backend produced structured session artifacts and the feedback payload was built from the stored interview turns.

## 6. Adaptive fallback after Gemini quota exhaustion

- Goal: prevent the interview experience from breaking when Gemini free-tier quota or rate-limit errors occurred.
- What was requested from the AI assistant: make the backend resilient when Gemini returned quota or rate-limit exhaustion errors instead of exposing a hard failure to the frontend.
- What was implemented: an adaptive fallback path was added to the interview service. The fallback is not described as Gemini-generated; instead, it classifies the latest answer and uses that classification to choose the next follow-up or topic transition.
- Important decisions: keep the experience usable even under service constraints and preserve a structured interview flow instead of crashing or returning a generic error.
- Validation performed: the system was tested after Gemini quota exhaustion issues caused HTTP 502-style failures, and the fallback path was verified to keep the interview running.

## 7. Frontend interview experience

- Goal: make the frontend feel like a real interview rather than a simple chat widget.
- What was requested from the AI assistant: improve the candidate experience, preserve question stability, and reduce interruptions from harmless acknowledgement messages.
- What was implemented: a chat-style UI was refined, candidate selection was wired to the backend, interview start and follow-up actions were connected to the API, and the UI preserved the current question until a substantive answer was submitted.
- Important decisions: acknowledgement-only replies such as "yes" or "okay" should not create unnecessary new questions.
- Validation performed: the frontend build succeeded and the interactive flow was verified through live requests.

## 8. Completion screen / structured feedback

- Goal: provide a clear ending to the interview experience instead of stopping after the last assistant reply.
- What was requested from the AI assistant: add a completion experience that summarizes the interview and shows structured feedback.
- What was implemented: a completion screen and feedback summary were added to show strengths, gaps, next steps, topic coverage, and skipped-question information.
- Important decisions: keep the feedback grounded in the stored interview turns rather than offering purely generic conclusions.
- Validation performed: the completion path was exercised as part of the end-to-end interview flow.

## 9. Conversational warm-up

- Goal: make the opening feel more personal and less like a quiz.
- What was requested from the AI assistant: add a brief, personalized warm-up before moving into technical assessment.
- What was implemented: the prompt and response flow were adjusted so the first turn could begin with a light conversational opener tied to the candidate profile.
- Important decisions: keep the warm-up short so the interview still reaches technical assessment quickly.
- Validation performed: the live interview endpoint returned a conversational opening followed by a technical interview direction.

## 10. Question stability / stale async response handling

- Goal: prevent old network responses from overwriting the latest interview state.
- What was requested from the AI assistant: make the frontend ignore stale asynchronous responses and keep the conversation stable.
- What was implemented: request identifiers were used to ensure that older responses would not replace newer state.
- Important decisions: keep the UI aligned with the latest user action and avoid flicker or state corruption.
- Validation performed: the frontend flow and chat state were exercised during the interview run.

## 11. Validation and debugging

- Goal: confirm that the app was still working after the interview-flow and fallback changes.
- What was requested from the AI assistant: verify syntax, build health, and live endpoint behavior.
- What was implemented: backend Python compilation checks, a frontend production build, and live interview endpoint validations were performed.
- Important decisions: document the truth of the build and runtime status rather than claiming unsupported test coverage.
- Validation performed: the backend compiled successfully, the frontend build succeeded, and the interview endpoint responded with a real interview reply.

## 12. Final audit / documentation

- Goal: prepare the repository for final submission by documenting the implementation and the development history without changing the application logic.
- What was requested from the AI assistant: produce a polished README and a truthful AI usage log suitable for a hackathon review.
- What was implemented: this README and the present PROMPTS.md file were created and aligned with the repository's actual structure and validations.
- Important decisions: avoid inventing deployment URLs, fake claims, or unsupported test suites.
- Validation performed: the documentation files were read back and the repository remained unchanged from an application-logic perspective.

## Notes

- No API keys, secrets, passwords, tokens, or private information are included in this document.
- AI coding assistants were used during development, and the work in this document reflects the actual repository history and validation steps performed.

## Deployment Note — Render Free Tier

The project is deployed using Render Free-tier services. After a period of inactivity, Render may spin down an instance. When the service is accessed again, the first request can take some time while the instance wakes up. This can appear as initial loading lag or delayed HTTP requests.

This cold-start delay is a hosting-tier behavior and does not by itself indicate that the application is broken. Once the service wakes up, the application should respond normally.

### Troubleshooting Lesson

During the hackathon, we verified the actual application and production configuration before considering a hosting-platform change.

A Render Free-tier cold start should **not be treated as a reason to migrate the project to Vercel, Netlify, or another platform**. Only an actual functional, configuration, or deployment problem should trigger a platform migration decision.

For a live demonstration, opening the deployed service shortly before the demo allows the Render instance to wake up in advance.
