"""上传模块路由，提供图片和报告上传接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.models import User
from app.services.file_service import save_file
from app.utils.deps import get_current_user


router = APIRouter(prefix="/api/upload", tags=["upload"])


def _build_file_url(request: Request, file_path: str) -> str:
    """根据相对路径构造可访问 URL。"""

    static_relative_path = file_path.removeprefix("uploads/").lstrip("/")
    return str(request.base_url).rstrip("/") + f"/static/{static_relative_path}"


@router.post("/image", summary="上传图片")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """上传图片文件。"""

    _ = current_user
    file_path = await save_file(file, "image")
    return {
        "file_path": file_path,
        "file_url": _build_file_url(request, file_path),
    }


@router.post("/report", summary="上传体检报告")
async def upload_report(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """上传图片或 PDF 报告。"""

    _ = current_user
    file_path = await save_file(file, "report")
    return {
        "file_path": file_path,
        "file_url": _build_file_url(request, file_path),
    }
