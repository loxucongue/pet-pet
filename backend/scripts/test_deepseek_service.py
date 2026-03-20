"""DeepSeek 服务联调脚本。"""

from __future__ import annotations

import argparse
import asyncio

from app.services.deepseek_service import (
    DeepSeekAuthenticationError,
    DeepSeekQuotaExceededError,
    DeepSeekRateLimitError,
    DeepSeekService,
    DeepSeekServiceError,
    DeepSeekTimeoutError,
)


SAMPLE_PET_INFO = {
    "nickname": "小橘",
    "species": "猫",
    "breed": "中华田园猫",
    "approximate_age": "大约 2 岁",
    "weight": 4.5,
    "is_neutered": True,
}

SAMPLE_OCR_DATA = """
姓名：小橘
检测项目：血常规 + 生化
白细胞 WBC：12.3（参考范围 5.5 - 19.5）
红细胞 RBC：6.2（参考范围 5.0 - 10.0）
血红蛋白 HGB：82（参考范围 93 - 153）
总蛋白 TP：79（参考范围 57 - 89）
谷丙转氨酶 ALT：96（参考范围 20 - 100）
肌酐 CREA：145（参考范围 71 - 212）
"""


async def run_interpret_test(service: DeepSeekService) -> None:
    """运行体检解读测试。"""

    result = await service.interpret_health_report(SAMPLE_OCR_DATA, SAMPLE_PET_INFO)
    print("=== interpret_health_report result ===")
    print(result)


async def run_chat_stream_test(service: DeepSeekService) -> None:
    """运行流式对话测试。"""

    print("=== chat_stream result ===")
    async for token in service.chat_stream(
        [
            {
                "role": "user",
                "content": "它今天有点咳嗽，但精神和食欲还可以，我应该先观察什么？",
            }
        ],
        SAMPLE_PET_INFO,
    ):
        print(token, end="", flush=True)
    print()


async def run_invalid_key_test(base_url: str | None) -> None:
    """运行无效 API Key 测试。"""

    service = DeepSeekService(api_key="invalid-key-for-test", base_url=base_url)
    try:
        await service.interpret_health_report(SAMPLE_OCR_DATA, SAMPLE_PET_INFO)
    except DeepSeekAuthenticationError as exc:
        print("=== invalid key test ===")
        print(f"捕获到预期认证错误：{exc}")
        return

    raise AssertionError("无效 API Key 测试未触发认证错误。")


async def main() -> None:
    """脚本入口。"""

    parser = argparse.ArgumentParser(description="DeepSeek 服务联调脚本")
    parser.add_argument(
        "--mode",
        choices=["interpret", "chat", "all", "invalid-key"],
        default="all",
        help="指定测试模式",
    )
    parser.add_argument(
        "--invalid-key-test",
        action="store_true",
        help="附加执行一次无效 API Key 测试",
    )
    args = parser.parse_args()

    try:
        if args.mode == "invalid-key":
            await run_invalid_key_test(None)
            return

        service = DeepSeekService()

        if args.mode in {"interpret", "all"}:
            await run_interpret_test(service)

        if args.mode in {"chat", "all"}:
            await run_chat_stream_test(service)

        if args.invalid_key_test:
            await run_invalid_key_test(service.base_url)
    except (
        DeepSeekAuthenticationError,
        DeepSeekQuotaExceededError,
        DeepSeekRateLimitError,
        DeepSeekTimeoutError,
        DeepSeekServiceError,
    ) as exc:
        print(f"DeepSeek 调用失败：{exc}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
