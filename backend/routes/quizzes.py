"""Quiz generation and hosted-data routes."""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from backend.deps import get_cfg, get_current_session
from backend.ludwitt.client import LudwittError
from backend.ludwitt.credits import LudwittCreditsClient
from backend.ludwitt.data import LudwittDataClient
from config import AppConfig, LudwittLLMClient
from ecs.services.quiz_service import QuizService

router = APIRouter(prefix="/api", tags=["api"])

QUIZ_COLLECTION = "quiz_runs"


def _apply_session_cookie(request: Request, response: Dict[str, Any]) -> Dict[str, Any]:
    return response


@router.get("/credits/balance")
def credits_balance(
    session: Dict[str, Any] = Depends(get_current_session),
):
    client = LudwittCreditsClient()
    try:
        return client.get_balance(session["access_token"])
    except LudwittError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/storage/usage")
def storage_usage(session: Dict[str, Any] = Depends(get_current_session)):
    client = LudwittDataClient()
    try:
        return client.usage(session["access_token"])
    except LudwittError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/quizzes/history")
def quiz_history(
    limit: int = 20,
    session: Dict[str, Any] = Depends(get_current_session),
):
    client = LudwittDataClient()
    try:
        payload = client.list_documents(
            session["access_token"],
            QUIZ_COLLECTION,
            limit=min(limit, 50),
            order_by="-updatedAt",
        )
        docs = []
        for doc in payload.get("docs", []):
            docs.append(
                {
                    "doc_id": doc.get("docId"),
                    "data": doc.get("data"),
                    "updated_at": doc.get("updatedAt"),
                }
            )
        return {"docs": docs, "next_cursor": payload.get("nextCursor")}
    except LudwittError as exc:
        if exc.status_code == 404:
            return {"docs": [], "next_cursor": None}
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/quizzes/generate")
async def generate_quiz(
    request: Request,
    pdf: UploadFile = File(...),
    n_questions: int = Form(10),
    offline: bool = Form(False),
    session: Dict[str, Any] = Depends(get_current_session),
    cfg: AppConfig = Depends(get_cfg),
):
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    n_questions = max(5, min(n_questions, 30))
    access_token = session["access_token"]

    if not offline:
        credits = LudwittCreditsClient(cfg)
        try:
            balance = credits.get_balance(access_token)
        except LudwittError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        if balance["spendable_cents"] <= 0:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_paid_credits",
                    "top_up_url": f"{cfg.ludwitt_base_url}/account/credits",
                    "spendable_cents": balance["spendable_cents"],
                },
            )

    suffix = os.path.splitext(pdf.filename)[1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await pdf.read())
        pdf_path = tmp.name

    try:
        if offline:
            service = QuizService(cfg=cfg)
            result = service.generate(
                pdf_path,
                n_questions=n_questions,
                offline=True,
                source_name=pdf.filename,
            )
        else:
            llm = LudwittLLMClient(access_token, cfg)
            service = QuizService(llm=llm, cfg=cfg)
            try:
                result = service.generate(
                    pdf_path,
                    n_questions=n_questions,
                    offline=False,
                    source_name=pdf.filename,
                )
            except LudwittError as exc:
                if exc.status_code == 402:
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": exc.error,
                            "code": exc.code,
                            "details": exc.details,
                            "top_up_url": f"{cfg.ludwitt_base_url}/account/credits",
                        },
                    ) from exc
                raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

        compact = QuizService.compact_for_storage(result)
        data_client = LudwittDataClient(cfg)
        doc_id = result["run_id"]
        try:
            stored = data_client.put_document(
                access_token,
                QUIZ_COLLECTION,
                doc_id,
                compact,
            )
            result["storage"] = stored
        except LudwittError as exc:
            result["storage_error"] = str(exc)

        if hasattr(request.state, "new_session_cookie"):
            result["_session_refreshed"] = True

        return result
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
