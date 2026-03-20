"""Coze OCR 服务联调脚本。"""

from __future__ import annotations

import argparse
import asyncio
import json

from app.services.coze_ocr_service import (
    CozeOCRInputError,
    CozeOCRService,
    CozeOCRServiceError,
)


async def main() -> None:
    """脚本入口。"""

    parser = argparse.ArgumentParser(description="Coze OCR 服务联调脚本")
    parser.add_argument("--file-path", required=True, help="本地文件路径或公网 URL")
    parser.add_argument(
        "--file-type",
        required=True,
        choices=["image", "pdf"],
        help="文件类型",
    )
    args = parser.parse_args()

    service = CozeOCRService()

    try:
        result = await service.recognize_report(args.file_path, args.file_type)
    except CozeOCRInputError as exc:
        print(f"Coze OCR 输入错误：{exc}")
        raise
    except CozeOCRServiceError as exc:
        print(f"Coze OCR 调用失败：{exc}")
        raise

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
