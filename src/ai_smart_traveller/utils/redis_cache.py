import json
import logging
from typing import Any, Dict, Optional

from .cache import Cache
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RedisCache(Cache):
    """基于 Redis 的缓存实现"""

    def __init__(
        self,
        ttl_seconds: int = 300,
        name: str = "default",
    ):
        """
        Args:
            ttl_seconds: 缓存过期时间（秒）
            name: 缓存名称，用于日志
        """
        self._ttl = ttl_seconds
        self._name = name

        # 使用统一的Redis客户端
        self._redis = get_redis_client()
        logger.info(f"[{name}] Redis缓存初始化成功")

    def _get_key(self, key: str) -> str:
        """获取带命名空间的键"""
        return f"{self._name}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            data = self._redis.get(self._get_key(key))
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"[{self._name}] Redis获取缓存失败: {e}")
            return None

    def set(self, key: str, value: Any):
        """设置缓存值"""
        try:
            data = json.dumps(value, ensure_ascii=False)
            self._redis.setex(self._get_key(key), self._ttl, data)
        except Exception as e:
            logger.error(f"[{self._name}] Redis设置缓存失败: {e}")

    def delete(self, key: str):
        """删除指定缓存"""
        try:
            self._redis.delete(self._get_key(key))
        except Exception as e:
            logger.error(f"[{self._name}] Redis删除缓存失败: {e}")

    def clear(self):
        """清空所有缓存"""
        try:
            pattern = f"{self._name}:*"
            keys = self._redis.keys(pattern)
            if keys:
                self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"[{self._name}] Redis清空缓存失败: {e}")

    def exists(self, key: str) -> bool:
        """检查键是否存在且未过期"""
        try:
            return bool(self._redis.exists(self._get_key(key)))
        except Exception as e:
            logger.error(f"[{self._name}] Redis检查键失败: {e}")
            return False

    def ttl(self, key: str) -> int:
        """获取键的剩余生存时间（秒）"""
        try:
            return self._redis.ttl(self._get_key(key))
        except Exception as e:
            logger.error(f"[{self._name}] Redis获取TTL失败: {e}")
            return 0

    @property
    def size(self) -> int:
        """获取当前缓存数量"""
        try:
            return len(self._redis.keys(f"{self._name}:*"))
        except Exception as e:
            logger.error(f"[{self._name}] Redis获取缓存数量失败: {e}")
            return 0

    @property
    def memory_info(self) -> Dict[str, Any]:
        """获取内存使用信息"""
        try:
            info = self._redis.info(section="memory")
            return {
                "items": self.size,
                "memory_bytes": info.get("used_memory", 0),
                "memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "max_memory": info.get("maxmemory", 0),
                "max_memory_mb": round(info.get("maxmemory", 0) / 1024 / 1024, 2),
                "ttl_seconds": self._ttl,
            }
        except Exception as e:
            logger.error(f"[{self._name}] Redis获取内存信息失败: {e}")
            return {
                "items": 0,
                "memory_bytes": 0,
                "memory_mb": 0,
                "max_memory": 0,
                "max_memory_mb": 0,
                "ttl_seconds": self._ttl,
            }
