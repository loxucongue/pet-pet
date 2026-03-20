"""文件服务，负责上传文件校验与落盘。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import HTTPException, UploadFile, status


BASE_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
REPORT_EXTENSIONS = IMAGE_EXTENSIONS | {".pdf"}
IMAGE_MAX_SIZE = 10 * 1024 * 1024
REPORT_MAX_SIZE = 20 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def _validate_extension(filename: str | None, file_category: str) -> str:
    """校验文件扩展名是否合法。"""

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名无效。",
        )

    extension = Path(filename).suffix.lower()
    allowed_extensions = IMAGE_EXTENSIONS if file_category == "image" else REPORT_EXTENSIONS
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件类型不支持。",
        )
    return extension


def _resolve_target_directory(file_category: str) -> Path:
    """根据文件类别生成目标存储目录。"""

    if file_category == "image":
        category_dir = "images"
    elif file_category == "report":
        category_dir = "reports"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件分类无效。",
        )

    date_dir = datetime.now().strftime("%Y-%m-%d")
    target_dir = BASE_UPLOAD_DIR / category_dir / date_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


async def save_file(file: UploadFile, file_category: str) -> str:
    """保存上传文件并返回相对路径。"""

    extension = _validate_extension(file.filename, file_category)
    max_size = IMAGE_MAX_SIZE if file_category == "image" else REPORT_MAX_SIZE
    target_dir = _resolve_target_directory(file_category)
    target_filename = f"{uuid4().hex}{extension}"
    target_path = target_dir / target_filename

    file_size = 0
    try:
        async with aiofiles.open(target_path, "wb") as output_file:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="文件大小超出限制。",
                    )
                await output_file.write(chunk)
    except Exception:
        if target_path.exists():
            target_path.unlink()
        raise
    finally:
        await file.close()

    relative_path = target_path.relative_to(BASE_UPLOAD_DIR.parent).as_posix()
    return relative_path

