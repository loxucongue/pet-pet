"""应用配置管理，统一从 .env 读取环境变量。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """集中管理后端运行配置。"""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="pppet backend", alias="APP_NAME")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    debug: bool = Field(default=False, alias="APP_DEBUG")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_user: str = Field(default="root", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_name: str = Field(default="pppet", alias="DB_NAME")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    database_url_sync: str | None = Field(default=None, alias="DATABASE_URL_SYNC")

    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str | None = Field(default=None, alias="DEEPSEEK_BASE_URL")
    coze_api_key: str | None = Field(default=None, alias="COZE_API_KEY")
    secret_key: str | None = Field(default=None, alias="SECRET_KEY")

    cors_allow_origin_regex: str = Field(
        default=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        alias="CORS_ALLOW_ORIGIN_REGEX",
    )
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

    @model_validator(mode="after")
    def build_database_urls(self) -> "Settings":
        """根据 DB_* 参数补全并校验数据库连接串。"""

        if self.db_name != "pppet":
            raise ValueError("DB_NAME 必须固定为 pppet，避免影响同一 MySQL 实例中的其他数据库。")

        if not self.database_url:
            self.database_url = (
                f"mysql+aiomysql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

        if not self.database_url_sync:
            self.database_url_sync = (
                f"mysql+pymysql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

        self._validate_database_name(self.database_url, "DATABASE_URL")
        self._validate_database_name(self.database_url_sync, "DATABASE_URL_SYNC")
        return self

    def _validate_database_name(self, database_url: str | None, field_name: str) -> None:
        """确保所有连接串都显式指向 pppet 数据库。"""

        if not database_url:
            raise ValueError(f"{field_name} 未配置。")

        database_name = urlsplit(database_url).path.lstrip("/")
        if database_name != self.db_name:
            raise ValueError(
                f"{field_name} 必须指向数据库 {self.db_name}，当前为 {database_name or '未指定'}。"
            )


@lru_cache
def get_settings() -> Settings:
    """缓存配置对象，避免重复解析 .env。"""

    return Settings()


settings = get_settings()
