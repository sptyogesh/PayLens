"""GET /report.pdf and GET /report/data: the CA report for a dashboard period (005 contracts).

Both are rate limited together. AI problems never change the status (the summary falls back).
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.ai.llm import LlmClient
from app.api.deps import get_llm, rate_limit
from app.common.constants import (
    RATE_LIMIT_LLM_GLOBAL,
    RATE_LIMIT_REPORT,
    REPORT_FILE_NAME,
    REPORT_MEDIA_TYPE,
)
from app.common.dates import ist_date, utc_now
from app.common.periods import DEFAULT_PERIOD, DashboardPeriod
from app.db import get_session
from app.reports.ca_report import render_pdf
from app.schemas.report import ReportData
from app.services.report_service import build_report_data

router = APIRouter(
    tags=["report"],
    dependencies=[Depends(rate_limit("report", RATE_LIMIT_REPORT, RATE_LIMIT_LLM_GLOBAL))],
)

PDF_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {"content": {REPORT_MEDIA_TYPE: {}}, "description": "The CA report PDF."}
}


@router.get("/report/data")
def report_data(
    session: Annotated[Session, Depends(get_session)],
    llm: Annotated[LlmClient, Depends(get_llm)],
    period: DashboardPeriod = DEFAULT_PERIOD,
) -> ReportData:
    return build_report_data(session, llm, period, utc_now())


@router.get("/report.pdf", response_class=Response, responses=PDF_RESPONSE)
def report_pdf(
    session: Annotated[Session, Depends(get_session)],
    llm: Annotated[LlmClient, Depends(get_llm)],
    period: DashboardPeriod = DEFAULT_PERIOD,
) -> Response:
    now = utc_now()
    data = build_report_data(session, llm, period, now)
    name = REPORT_FILE_NAME.format(period=period.value, day=ist_date(now).isoformat())
    return Response(
        content=render_pdf(data),
        media_type=REPORT_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
