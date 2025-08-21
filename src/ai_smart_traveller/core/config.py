from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str
    APP_VERSION: str
    API_PREFIX: str

    # 基础配置
    DEBUG: str = "false"  # 改为字符串，手动解析

    # 服务配置
    HOST: str
    PORT: int
    WORKERS: int

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"

    # LLM 配置
    DEFAULT_LLM_TYPE: str = "gpt4"  # 默认使用GPT-4

    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None  # 可选，不配置也能运行
    OPENAI_MODEL_NAME: str = "gpt-4"  # GPT-4 默认模型
    OPENAI_GPT5_MODEL_NAME: str = "gpt-5"  # GPT-5 默认模型
    OPENAI_TEMPERATURE: float = 0.7

    # CloseAI代理配置
    OPENAI_API_BASE: Optional[str] = None  # CloseAI代理地址

    # 通义千问配置（使用DASHSCOPE API）
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QIANWEN_MODEL_NAME: str = "qwen-turbo"
    QIANWEN_TEMPERATURE: float = 0.7

    # Redis配置
    USE_REDIS_CACHE: str = "true"  # 改为字符串，手动解析
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # 企业微信配置
    WECOM_CORP_ID: Optional[str] = None
    WECOM_CORP_SECRET: Optional[str] = None
    WECOM_AGENT_ID: Optional[str] = None
    WECOM_AGENT_SECRET: Optional[str] = None
    WECOM_TOKEN: Optional[str] = None
    WECOM_ENCODING_AES_KEY: Optional[str] = None

    # 阿里云OSS配置
    OSS_ENDPOINT: str = "https://oss-cn-shanghai.aliyuncs.com"
    OSS_ACCESS_KEY: str = "your_access_key"
    OSS_SECRET_KEY: str = "your_secret_key"
    OSS_BUCKET: str = "your_bucket"

    # 阿里云语音识别配置
    ALIYUN_APP_KEY: Optional[str] = None
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None

    # 语音识别服务配置
    VOICE_SERVICE_TYPE: str = "whisper"  # 可选: "whisper", "aliyun"

    # 聊天会话管理配置
    CHAT_MAX_MESSAGES: int = 20  # 最大消息数量
    CHAT_MAX_TOKENS: int = 4000  # 最大token数量（估算）
    CHAT_SESSION_TIMEOUT_HOURS: int = 24  # 会话超时时间（小时）
    CHAT_CLEANUP_INTERVAL_HOURS: int = 1  # 清理间隔（小时）

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    settings = Settings()

    # 手动解析布尔值
    def parse_bool(value: str) -> bool:
        if isinstance(value, str):
            return value.lower().strip().split("#")[0].strip() in ("true", "1", "t", "yes", "y")
        return bool(value)

    # 转换为布尔值
    settings.DEBUG = parse_bool(settings.DEBUG)
    settings.USE_REDIS_CACHE = parse_bool(settings.USE_REDIS_CACHE)

    return settings


# 创建全局配置实例
settings = get_settings()
