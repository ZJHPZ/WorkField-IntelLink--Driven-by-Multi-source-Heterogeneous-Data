"""应用配置 —— 从 .env / 环境变量读取，pydantic-settings 管理。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置，所有值可从环境变量或 .env 文件覆盖。"""

    # ── 应用 ──
    APP_ENV: Literal["development", "production", "test"] = "development"
    APP_DEBUG: bool = True
    APP_TITLE: str = "职域智联图谱 API"
    APP_VERSION: str = "2.0.0"

    # ── 星火 LLM ──
    SPARK_API_PASSWORD: str = ""
    SPARK_BASE_URL: str = "https://spark-api-open.xf-yun.com/agent/v1/"
    SPARK_MODEL: str = "spark-x"

    # ── Neo4j ──
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "zhiyu2024"
    NEO4J_DATABASE: str = "neo4j"

    # ── MySQL ──
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "zhiyv"

    # ── 数据路径 ──
    DATA_DIR: Path = Path(__file__).parent.parent / "data" / "jd"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
