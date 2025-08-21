"""
统一的Redis客户端管理模块
"""

import logging

from redis import Redis

from ..core.config import get_settings

logger = logging.getLogger(__name__)

# 全局Redis客户端实例
_redis_client = None


def get_redis_client() -> Redis:
    """
    获取Redis客户端实例（单例模式）

    Returns:
        Redis客户端实例
    """
    global _redis_client

    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        logger.info("Redis客户端初始化完成")

    return _redis_client


def close_redis_client():
    """关闭Redis客户端连接"""
    global _redis_client

    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis客户端连接已关闭")
