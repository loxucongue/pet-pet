"""体检报告分析服务。"""

from __future__ import annotations

import json
from typing import Any, Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import HealthReport, Pet, User
from app.schemas.health_report import HealthReportIndicatorsUpdate
from app.services.coze_ocr_service import CozeOCRService, CozeOCRServiceError
from app.services.deepseek_service import DeepSeekService, DeepSeekServiceError
from app.services.pet_service import get_pet_by_id
from app.services.quota_service import (
    AnalysisQuotaExceededError,
    consume_analysis_quota,
    ensure_analysis_quota,
    get_analysis_remaining,
)


async def analyze_report(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
    file_path: str,
    file_type: str,
    *,
    coze_ocr_service: CozeOCRService | Any | None = None,
    deepseek_service: DeepSeekService | Any | None = None,
) -> HealthReport:
    """执行体检报告 OCR 识别与 AI 解读完整流程。"""

    pet = await get_pet_by_id(session, pet_id, user_id)
    user = await _get_user_by_id(session, user_id)
    await ensure_analysis_quota(session, user)

    report = HealthReport(
        pet_id=pet.id,
        original_file_path=file_path,
        file_type=file_type,
        status="pending",
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)

    try:
        report.status = "processing"
        await session.commit()
        await session.refresh(report)

        ocr_service = coze_ocr_service or CozeOCRService()
        ai_service = deepseek_service or DeepSeekService()

        ocr_result = await ocr_service.recognize_report(file_path, file_type)
        report.ocr_result_json = json.dumps(ocr_result, ensure_ascii=False)
        report.parsed_indicators_json = json.dumps(
            ocr_result.get("indicators") or [],
            ensure_ascii=False,
        )

        interpretation = await ai_service.interpret_health_report(
            _build_interpretation_source_text(
                raw_text=ocr_result.get("raw_text") or "",
                indicators=ocr_result.get("indicators") or [],
            ),
            _build_pet_info(pet),
        )

        report.ai_interpretation = interpretation
        report.status = "completed"
        await consume_analysis_quota(session, user)
        await session.commit()
        await session.refresh(report)
        return report
    except Exception as exc:  # noqa: BLE001
        report.status = "failed"
        await session.commit()
        raise _translate_health_exception(exc) from exc


async def get_report_list(
    session: AsyncSession,
    user_id: int,
    pet_id: int | None = None,
) -> Sequence[HealthReport]:
    """查询当前用户的体检报告列表。"""

    if pet_id is not None:
        await get_pet_by_id(session, pet_id, user_id)

    statement = (
        select(HealthReport)
        .join(Pet, HealthReport.pet_id == Pet.id)
        .options(selectinload(HealthReport.pet))
        .where(
            Pet.user_id == user_id,
            Pet.is_deleted.is_(False),
        )
        .order_by(HealthReport.created_at.desc(), HealthReport.id.desc())
    )
    if pet_id is not None:
        statement = statement.where(HealthReport.pet_id == pet_id)

    result = await session.scalars(statement)
    return result.all()


async def get_report_detail(
    session: AsyncSession,
    report_id: int,
    user_id: int,
) -> HealthReport:
    """查询单条体检报告详情。"""

    report = await session.scalar(
        select(HealthReport)
        .options(selectinload(HealthReport.pet))
        .where(HealthReport.id == report_id)
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="体检报告不存在。",
        )

    if report.pet is None or report.pet.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="体检报告不存在。",
        )

    if report.pet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该体检报告。",
        )

    return report


async def update_report_indicators(
    session: AsyncSession,
    report_id: int,
    user_id: int,
    indicators_data: HealthReportIndicatorsUpdate,
) -> HealthReport:
    """更新体检报告的结构化指标数据。"""

    report = await get_report_detail(session, report_id, user_id)
    report.parsed_indicators_json = json.dumps(
        [item.model_dump(exclude_none=True) for item in indicators_data.indicators],
        ensure_ascii=False,
    )
    await session.commit()
    await session.refresh(report)
    return report


async def reanalyze_report(
    session: AsyncSession,
    report_id: int,
    user_id: int,
    *,
    deepseek_service: DeepSeekService | Any | None = None,
) -> HealthReport:
    """基于当前指标数据重新触发 AI 解读。"""

    report = await get_report_detail(session, report_id, user_id)
    user = await _get_user_by_id(session, user_id)
    await ensure_analysis_quota(session, user)

    source_text = _build_reanalyze_source_text(report)
    if not source_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前报告缺少可用于重新解读的 OCR 或指标数据。",
        )

    try:
        ai_service = deepseek_service or DeepSeekService()
        interpretation = await ai_service.interpret_health_report(
            source_text,
            _build_pet_info(report.pet),
        )
        report.ai_interpretation = interpretation
        report.status = "completed"
        await consume_analysis_quota(session, user)
        await session.commit()
        await session.refresh(report)
        return report
    except Exception as exc:  # noqa: BLE001
        report.status = "failed"
        await session.commit()
        raise _translate_health_exception(exc) from exc


async def get_health_quota_summary(session: AsyncSession, user_id: int) -> dict[str, int]:
    """获取当前用户体检报告分析剩余额度。"""

    user = await _get_user_by_id(session, user_id)
    remaining = await get_analysis_remaining(session, user)
    return {"remaining": remaining}


async def _get_user_by_id(session: AsyncSession, user_id: int) -> User:
    """按 ID 获取用户。"""

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在。",
        )
    return user


def _build_pet_info(pet: Pet) -> dict[str, Any]:
    """构造 DeepSeek 所需宠物档案信息。"""

    return {
        "nickname": pet.nickname,
        "species": pet.species,
        "breed": pet.breed,
        "gender": pet.gender,
        "birthday": str(pet.birthday) if pet.birthday else None,
        "approximate_age": pet.approximate_age,
        "weight": pet.weight,
        "is_neutered": pet.is_neutered,
        "fur_color": pet.fur_color,
        "allergy_history": pet.allergy_history,
        "chronic_disease": pet.chronic_disease,
        "current_food_brand": pet.current_food_brand,
    }


def _build_interpretation_source_text(raw_text: str, indicators: list[dict[str, Any]]) -> str:
    """构造体检解读输入文本。"""

    parts: list[str] = []
    if raw_text.strip():
        parts.append(f"OCR 原始文本：\n{raw_text.strip()}")
    if indicators:
        parts.append(
            "结构化指标数据：\n"
            + json.dumps(indicators, ensure_ascii=False, indent=2)
        )
    return "\n\n".join(parts).strip()


def _build_reanalyze_source_text(report: HealthReport) -> str:
    """构造重新解读输入文本。"""

    parts: list[str] = []

    if report.ocr_result_json:
        try:
            parsed_ocr = json.loads(report.ocr_result_json)
        except json.JSONDecodeError:
            parsed_ocr = report.ocr_result_json

        if isinstance(parsed_ocr, dict):
            raw_text = str(parsed_ocr.get("raw_text") or "").strip()
            if raw_text:
                parts.append(f"OCR 原始文本：\n{raw_text}")
        elif isinstance(parsed_ocr, str) and parsed_ocr.strip():
            parts.append(f"OCR 原始文本：\n{parsed_ocr.strip()}")

    if report.parsed_indicators_json:
        try:
            parsed_indicators = json.loads(report.parsed_indicators_json)
        except json.JSONDecodeError:
            parsed_indicators = report.parsed_indicators_json

        if parsed_indicators:
            if isinstance(parsed_indicators, str):
                parts.append(f"结构化指标数据：\n{parsed_indicators}")
            else:
                parts.append(
                    "结构化指标数据：\n"
                    + json.dumps(parsed_indicators, ensure_ascii=False, indent=2)
                )

    return "\n\n".join(parts).strip()


def _translate_health_exception(exc: Exception) -> Exception:
    """将外部服务异常转为接口层可用异常。"""

    if isinstance(exc, AnalysisQuotaExceededError):
        return exc

    if isinstance(exc, HTTPException):
        return exc

    if isinstance(exc, CozeOCRServiceError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OCR识别失败：{exc}",
        )

    if isinstance(exc, DeepSeekServiceError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI解读失败：{exc}",
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="体检报告分析失败，请稍后重试。",
    )
