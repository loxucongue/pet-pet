"""创建项目专用的 pppet MySQL 数据库。"""

from __future__ import annotations

import pymysql

from app.config import settings


CREATE_DATABASE_SQL = (
    f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` "
    "DEFAULT CHARACTER SET utf8mb4 "
    "COLLATE utf8mb4_unicode_ci"
)


def main() -> None:
    """连接 MySQL 服务并确保 pppet 数据库存在。"""

    try:
        connection = pymysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            charset="utf8mb4",
            autocommit=True,
        )
    except pymysql.MySQLError as exc:
        raise SystemExit(f"MySQL 连接失败: {exc}") from exc

    try:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_DATABASE_SQL)
        print(
            f"数据库 `{settings.db_name}` 已创建或已存在，"
            "后续表结构只会迁移到该数据库。"
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
