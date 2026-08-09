# GNANEX AI — AI Technical Interview Agent

GNANEX AI is a full-stack interview agent that conducts personalized, multi-turn technical interviews based on a candidate's cohort journey, experience profile, and curriculum topics. The system combines a conversational frontend with a FastAPI backend and a Gemini-powered interview service, while maintaining a graceful fallback when Gemini quota or rate limits are unavailable.

## Problem statement / motivation

Technical interview experiences are often rigid, repetitive, and disconnected from the candidate's actual learning journey. A strong candidate can be reduced to a quiz-like interaction rather than a realistic technical conversation. GNANEX AI aims to improve that experience by creating a more human-style interviewer that uses candidate context, curriculum awareness, and follow-up adaptation to feel more natural and relevant.

## Solution overview

The project provides a chat-style interview experience where a candidate is first selected, then guided through a personalized warm-up and a curriculum-aware technical discussion. The backend tracks the session, stores interview turns, and builds structured feedback at the end. Gemini is used as the primary interviewer when available, while a deterministic adaptive fallback keeps the interview usable if model quota or rate-limit errors occur.

## Key features

- Personalized conversational warm-up
- Curriculum-aware technical questions
- Multi-turn contextual interview flow
- Adaptive follow-up questions
- Candidate-answer-aware interview progression
- Gemini AI integration for interview generation
- Adaptive fallback when Gemini quota or rate limits are unavailable
- Structured interview turn history and session persistence
- Topic and question evaluation throughout the interview
- Final strengths, gaps, and next-step feedback
- Skipped-question handling in the feedback summary
- Responsive interview UI

## Interview flow

1. Candidate selection
2. Personalized warm-up
3. Conversational interaction
4. Curriculum-based technical assessment
5. Adaptive follow-ups based on candidate answers
6. Interview completion and structured feedback

## Gemini and fallback architecture

Gemini is the primary AI interviewer when available. If Gemini returns quota or rate-limit exhaustion, the backend uses an adaptive fallback so the interview remains usable. The fallback is not described as Gemini-generated. Instead, it considers the latest candidate answer and classifies it as strong, partial, weak, don't know, pass, or unclear, then selects follow-ups and topic transitions based on that classification.

## Architecture

### Frontend

The frontend is built with Next.js, React, and TypeScript. It presents the interview experience in a chat-style UI, loads candidate data from the backend, and preserves conversation state while preventing acknowledgement-only replies from creating unnecessary question changes.

### Backend / API

The backend uses FastAPI to expose interview endpoints. The main routes are:

- POST /api/interview for starting or continuing an interview session
- GET /api/candidates for returning candidate metadata for selection

### Session / interview state

The session model stores the current interview state, question history, dialogue turns, evaluations, warm-up usage, technical question count, and completion state. This makes the conversation context-aware across follow-ups.

### Gemini service

The Gemini service is responsible for generating interview replies, prompting the interviewer with candidate context and curriculum information, and coordinating turn progression.

### Fallback behavior

When Gemini quota or rate-limit errors occur, the backend switches to an adaptive fallback path. This keeps the interview functional and preserves the structure of the conversation instead of exposing a hard failure to the frontend.

### Feedback generation

At completion, the system builds a structured feedback payload with a summary, strengths, gaps, next steps, topic coverage, and skipped-question information.

## Technology stack

The repository uses the following technologies that are actually present:

- Backend: Python 3, FastAPI, Uvicorn, Pydantic, python-dotenv, and Google Generative AI client libraries
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS, PostCSS, and ESLint

## Project structure

```text
backend/
  main.py
  requirements.txt
  app/
    models/session.py
    routes/interview.py
    services/
      data_loader.py
      gemini.py
      gemini_prompt.py

data/
  candidates.json
  curriculum.json

frontend/
  app/
    page.tsx
  components/
  public/
  package.json
```

## Local setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd dreamhackers-gnanex-ai
```

### 2. Create and activate a backend virtual environment

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Set environment variables

Create a local environment file for the backend and define the Gemini key:

```bash
export GEMINI_API_KEY=your_api_key_here
```

The backend also loads environment variables from the local backend environment file when present. Keep API keys local and never commit them.

### 5. Install frontend dependencies

```bash
cd frontend
npm install
```

### 6. Run the application locally

Start the backend from the repository root:

```bash
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in a separate terminal:

```bash
npm run dev -- --hostname 127.0.0.1 --port 3000
```

If the frontend is running on a different host or port than the backend, set NEXT_PUBLIC_API_BASE_URL to point to the backend origin. If it is not set, the frontend uses the same origin by default.

## Environment variables

- GEMINI_API_KEY: required for Gemini-backed interview generation. Keep it in a local environment file or shell session and never commit it.
- The repository already ignores .env and .env.* files for safety.

## Testing / validation

The following validations were performed for the current repository state:

- Python compilation check for the backend interview modules
- Frontend production build
- Live verification of the interview endpoint response flow
- Manual verification of interview behavior including warm-up, follow-ups, and acknowledgement handling

## Demo flow for judges

1. Start the backend and frontend.
2. Select a candidate from the candidate list.
3. Observe the personalized warm-up and initial interview question.
4. Respond to the interviewer with a technical answer.
5. Continue the conversation to see adaptive follow-ups and topic progression.
6. Finish the interview to review the structured feedback summary.

## Hackathon requirements mapping

The project is structured to satisfy the following hackathon requirements:

- Conversational technical interview: the system uses a warm-up plus multi-turn dialogue rather than a single-step quiz.
- Minimum 8 questions: the interview loop is designed to continue across multiple turns and maintain a question count in session state.
- At least 4 curriculum days/topics: the system loads curriculum content from data/curriculum.json and uses it to guide topic selection.
- Adaptive follow-ups: both the Gemini-based path and the fallback path adapt the next question to the latest answer.
- Conversation context: the backend persists session dialogue, turns, and interview state across requests.
- Structured feedback: the final response includes a feedback summary, strengths, gaps, next steps, and topic-related analysis.
- Required HTTP endpoint: the FastAPI backend exposes /api/interview and /api/candidates.

## Limitations / graceful degradation

Gemini quota or rate-limit issues can still occur in real-world use. In those cases, the fallback path keeps the interview functional and prevents a hard failure from breaking the experience. The fallback is intentionally simpler than the Gemini path, but it remains usable and structured.

## Security note

Never commit .env, API keys, or other secrets. The repository is configured to ignore local environment files.

## Future improvements

Possible next steps include richer analytics, wider curriculum coverage, more configurable difficulty tuning, and stronger fallback prompt refinement.

## AI-assisted development note

AI coding assistants were used during development. The development prompt history and AI-assisted workflow are documented in PROMPTS.md.

Deployment URL will be added before submission.
