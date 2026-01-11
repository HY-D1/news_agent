from __future__ import annotations

from fastapi import APIRouter

from app.core.schemas import DigestRequest, DigestResponse
from app.pipeline.orchestrator import build_digest

router = APIRouter(tags=["digest"])


@router.post("/digest", response_model=DigestResponse)
def digest(req: DigestRequest) -> DigestResponse:
    return build_digest(req)
