"""POST /fira/upload (one raw PDF per request, rate limited) and GET /fira (004 contracts).

No multipart: the body is the PDF itself. It is read only up to FIRA_MAX_BYTES + 1 bytes, so a
larger file is rejected without reading it all. Per-file problems are 200 with an outcome.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.ai.llm import LlmClient
from app.api.deps import get_llm, rate_limit
from app.common.constants import (
    FIRA_FILE_NAME_MAX,
    FIRA_MAX_BYTES,
    RATE_LIMIT_FIRA,
    RATE_LIMIT_LLM_GLOBAL,
)
from app.db import get_session, get_session_factory
from app.schemas.fira import FiraListOut, UploadResultOut
from app.services.fira_service import list_firas, upload

router = APIRouter(tags=["fira"])

FileName = Annotated[
    str, Query(min_length=1, max_length=FIRA_FILE_NAME_MAX, pattern=r"\S", description="name.pdf")
]


async def read_limited(request: Request, limit: int) -> bytes:
    """The body, stopping once more than `limit` bytes have arrived."""
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        chunks.append(chunk)
        size += len(chunk)
        if size > limit:
            break
    return b"".join(chunks)[: limit + 1]


@router.post(
    "/fira/upload",
    dependencies=[Depends(rate_limit("fira", RATE_LIMIT_FIRA, RATE_LIMIT_LLM_GLOBAL))],
)
async def post_fira_upload(
    request: Request,
    file_name: FileName,
    factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
    llm: Annotated[LlmClient, Depends(get_llm)],
) -> UploadResultOut:
    body = await read_limited(request, FIRA_MAX_BYTES)
    content_type = request.headers.get("content-type", "")
    return await run_in_threadpool(upload, factory, llm, file_name, body, content_type)


@router.get("/fira")
def get_firas(session: Annotated[Session, Depends(get_session)]) -> FiraListOut:
    return list_firas(session)
