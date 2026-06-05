"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.auth import router as auth_router
from backend.routes.quizzes import router as quiz_router
from config import AppConfig

cfg = AppConfig()


def _cors_origins() -> list[str]:
    origins = {
        cfg.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    if cfg.cors_origins:
        origins.update(o.strip() for o in cfg.cors_origins.split(",") if o.strip())
    return sorted(origins)


app = FastAPI(
    title="QuickQuiz API",
    description="Ludwitt-integrated educational quiz generator",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(quiz_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "quickquiz-api"}
