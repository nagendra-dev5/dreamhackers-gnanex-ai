from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parent / ".env")

from backend.app.routes.interview import router as interview_router

app = FastAPI(
    title="GNANEX Interview API",
    version="0.1.0",
    description="Backend foundation for GNANEX technical interview sessions.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dreamhackers-gnanex-ai.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router)
