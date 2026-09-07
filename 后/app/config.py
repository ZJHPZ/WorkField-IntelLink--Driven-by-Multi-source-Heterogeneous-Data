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

    # ── 简历解析模式 ──
    # pseudo = 确定性伪解析（默认；无需智能体，关键字嗅探模拟分析效果）
    # agent  = 走 MultiAgentSystem(EXTRACT_SKILLS) 真智能体（需配置星火并联网）
    RESUME_PARSE_MODE: Literal["pseudo", "agent"] = "pseudo"

    # ── 星火 LLM ──
    SPARK_API_PASSWORD: str = ""
    SPARK_BASE_URL: str = "https://spark-api-open.xf-yun.com/agent/v1/"
    SPARK_MODEL: str = "spark-x"

    # ── Coze 智能体「帕克」（AI 职业顾问外部智能体）──
    COZE_API_TOKEN: str = ""
    COZE_API_URL: str = "https://886xv55s2h.coze.site/stream_run"

    # ── 讯飞虚拟人（数字人）──
    # apiKey/apiSecret 只用于服务端签名 signedUrl，绝不外发到前端/仓库。
    # 凭证齐全时 GET /api/enterprise/avatar/signed-url 返回 configured:true；否则前端走演示模式。
    AVATAR_APP_ID: str = ""
    AVATAR_API_KEY: str = ""
    AVATAR_API_SECRET: str = ""
    AVATAR_SCENE_ID: str = ""
    AVATAR_AVATAR_ID: str = ""
    AVATAR_VOICE_ID: str = ""
    AVATAR_HOST: str = "vms.cn-huadong-1.xf-yun.com"
    AVATAR_START_PATH: str = "/v1/private/vms2d_start"

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
