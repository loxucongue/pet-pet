"""重置开发环境数据库并恢复默认数据。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.init_db import main as init_db_main


BASE_DIR = Path(__file__).resolve().parents[1]


def run_command(args: list[str]) -> None:
    """执行命令，失败时直接抛出异常。"""

    subprocess.run(
        args,
        cwd=BASE_DIR,
        check=True,
    )


def main() -> None:
    """执行数据库回滚、重建和初始数据插入。"""

    run_command([sys.executable, "-m", "alembic", "downgrade", "base"])
    run_command([sys.executable, "-m", "alembic", "upgrade", "head"])
    init_db_main()
    print("数据库已重置并恢复初始数据。")


if __name__ == "__main__":
    main()

