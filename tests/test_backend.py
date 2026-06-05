"""Backend and Ludwitt integration tests."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.ludwitt.client import LudwittError
from backend.main import app
from backend.session import SessionManager
from ecs.services.quiz_service import QuizService


class TestSessionManager:
    def test_state_roundtrip(self):
        manager = SessionManager()
        state = manager.create_state()
        signed = manager.sign_state(state)
        assert manager.verify_state(signed, state) is True
        assert manager.verify_state(signed, "wrong-state") is False

    def test_session_roundtrip(self):
        manager = SessionManager()
        token_payload = {
            "access_token": "lt_test",
            "refresh_token": "lr_test",
            "expires_in": 3600,
            "scope": "profile credits:spend",
        }
        userinfo = {"sub": "user-1", "email": "student@example.com", "name": "Student"}
        signed = manager.create_session(token_payload, userinfo)
        loaded = manager.load_session(signed)
        assert loaded is not None
        assert loaded["user"]["sub"] == "user-1"
        assert loaded["access_token"] == "lt_test"


class TestQuizService:
    def test_compact_for_storage_limits_payload(self):
        result = {
            "run_id": "abc",
            "source_name": "lecture.pdf",
            "created_at": "2026-06-05T00:00:00+00:00",
            "mode": "online",
            "llm_calls_used": 1,
            "estimated_cost": 0.04,
            "analysis": {
                "concepts": [f"concept-{i}" for i in range(20)],
                "learning_objectives": [f"obj-{i}" for i in range(10)],
            },
            "statistics": {
                "basic_stats": {"word_count": 1200},
                "readability": {"readability_level": "Standard"},
            },
            "quiz": {"count": 10, "questions": [{"type": "mcq", "question": "Q?", "answer": "A"}]},
        }
        compact = QuizService.compact_for_storage(result)
        assert compact["runId"] == "abc"
        assert len(compact["analysis"]["concepts"]) <= 10
        assert len(compact["analysis"]["learningObjectives"]) <= 6
        assert compact["quiz"]["count"] == 10


class TestLudwittError:
    def test_error_string(self):
        err = LudwittError(
            status_code=402,
            error="insufficient_paid_credits",
            description="No paid credits",
            code="INSUFFICIENT_PAID_CREDITS",
        )
        assert "insufficient_paid_credits" in str(err)


class TestAPI:
    def test_health(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_me_requires_auth(self):
        client = TestClient(app)
        response = client.get("/auth/me")
        assert response.status_code == 401

    @patch("backend.routes.quizzes.LudwittCreditsClient.get_balance")
    @patch("backend.routes.quizzes.QuizService.generate")
    @patch("backend.routes.quizzes.LudwittDataClient.put_document")
    def test_generate_requires_auth_cookie(
        self,
        mock_put,
        mock_generate,
        mock_balance,
    ):
        manager = SessionManager()
        signed = manager.create_session(
            {
                "access_token": "lt_test",
                "refresh_token": "lr_test",
                "expires_in": 3600,
                "scope": "profile credits:spend data:write",
            },
            {"sub": "user-1", "email": "student@example.com", "name": "Student"},
        )
        mock_balance.return_value = {"spendable_cents": 100, "balance_cents": 100}
        mock_generate.return_value = {
            "run_id": "run-1",
            "source_name": "lecture.pdf",
            "created_at": "2026-06-05T00:00:00+00:00",
            "mode": "offline",
            "quiz": {"count": 1, "questions": []},
            "analysis": {"concepts": [], "learning_objectives": []},
            "statistics": {},
            "llm_calls_used": 0,
            "estimated_cost": 0.0,
        }
        mock_put.return_value = {"etag": "abc"}

        client = TestClient(app)
        client.cookies.set("quickquiz_session", signed)

        files = {"pdf": ("lecture.pdf", b"%PDF-1.4 test", "application/pdf")}
        data = {"n_questions": "5", "offline": "true"}
        response = client.post("/api/quizzes/generate", files=files, data=data)
        assert response.status_code == 200
        payload = response.json()
        assert payload["run_id"] == "run-1"
