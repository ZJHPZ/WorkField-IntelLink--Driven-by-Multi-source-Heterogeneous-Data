"""苏格拉底服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class SocraticSettings(BaseSettings):
    model_config = {"extra": "ignore", "env_file": ".env", "case_sensitive": True}

    APP_NAME: str = "苏格拉底引导反思服务"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # 讯飞星火 X2-Flash (OpenAI 兼容接口)
    SPARK_API_PASSWORD: str = os.getenv("SPARK_API_PASSWORD", "")
    SPARK_API_URL: str = os.getenv(
        "SPARK_API_URL",
        "https://spark-api-open.xf-yun.com/agent/v1/chat/completions",
    )
    SPARK_MODEL: str = os.getenv("SPARK_MODEL", "spark-x")

    SELF_API_URL: str = os.getenv("SELF_API_URL", "http://localhost:8001")


@lru_cache()
def get_settings() -> SocraticSettings:
    return SocraticSettings()


settings = get_settings()
