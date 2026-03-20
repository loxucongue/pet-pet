"""健康分析模块路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas.health_report import (
    HealthAnalyzeRequest,
    HealthQuotaResponse,
    HealthReportIndicatorsUpdate,
    HealthReportListResponse,
    HealthReportResponse,
)
from app.services.health_service import (
    analyze_report,
    get_health_quota_summary,
    get_report_detail,
    get_report_list,
    reanalyze_report,
    update_report_indicators,
)
from app.services.quota_service import AnalysisQuotaExceededError
from app.utils.deps import get_current_user


router = APIRouter(prefix="/api/health", tags=["health"])


@router.post("/analyze", response_model=HealthReportResponse, summary="上传并分析体检报告")
async def analyze_report_route(
    payload: HealthAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> HealthReportResponse | JSONResponse:
    """上传并分析体检报告。"""

    try:
        report = await analyze_report(
            session,
            payload.pet_id,
            current_user.id,
            payload.file_path,
            payload.file_type,
        )
    except AnalysisQuotaExceededError as exc:
        return JSONResponse(
            status_code=403,
            content={"detail": exc.detail, "remaining": exc.remaining},
        )

    return HealthReportResponse.model_validate(report)


@router.get("/reports", response_model=HealthReportListResponse, summary="查询体检报告历史")
async def list_health_reports_route(
    pet_id: int | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> HealthReportListResponse:
    """查询当前用户的体检报告历史。"""

    reports = await get_report_list(session, current_user.id, pet_id)
    return HealthReportListResponse(
        items=[HealthReportResponse.model_validate(report) for report in reports],
        total=len(reports),
    )


@router.get("/reports/{report_id}", response_model=HealthReportResponse, summary="查询体检报告详情")
async def get_health_report_route(
    report_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> HealthReportResponse:
    """查询单条体检报告详情。"""

    report = await get_report_detail(session, report_id, current_user.id)
    return HealthReportResponse.model_validate(report)


@router.put(
    "/reports/{report_id}/indicators",
    response_model=HealthReportResponse,
    summary="修改体检报告指标数据",
)
async def update_health_report_indicators_route(
    report_id: int,
    payload: HealthReportIndicatorsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> HealthReportResponse:
    """更新结构化指标数据，不消耗 AI 额度。"""

    report = await update_report_indicators(session, report_id, current_user.id, payload)
    return HealthReportResponse.model_validate(report)


@router.post(
    "/reports/{report_id}/reanalyze",
    response_model=HealthReportResponse,
    summary="重新触发 AI 解读",
)
async def reanalyze_health_report_route(
    report_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> HealthReportResponse | JSONResponse:
    """基于当前 OCR/指标数据重新 AI 解读。"""

    try:
        report = await reanalyze_report(session, report_id, current_user.id)
    except AnalysisQuotaExceededError as exc:
        return JSONResponse(
            status_code=403,
            content={"detail": exc.detail, "remaining": exc.remaining},
        )

    return HealthReportResponse.model_validate(report)


@router.get("/quota", response_model=HealthQuotaResponse, summary="查询健康分析剩余额度")
async def get_health_quota_route(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> HealthQuotaResponse:
    """查询当前用户的 AI 分析剩余额度。"""

    quota = await get_health_quota_summary(session, current_user.id)
    return HealthQuotaResponse.model_validate(quota)
