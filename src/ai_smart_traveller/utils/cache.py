import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Cache(ABC):
    """缓存抽象基类"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any):
        """设置缓存值"""
        pass

    @abstractmethod
    def delete(self, key: str):
        """删除指定缓存"""
        pass

    @abstractmethod
    def clear(self):
        """清空所有缓存"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在且未过期"""
        pass

    @abstractmethod
    def ttl(self, key: str) -> int:
        """获取键的剩余生存时间（秒）"""
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        """获取当前缓存数量"""
        pass

    @property
    @abstractmethod
    def memory_info(self) -> Dict[str, Any]:
        """获取内存使用信息"""
        pass


def create_cache(**kwargs) -> "Cache":
    """
    创建缓存实例

    Args:
        **kwargs: 传递给RedisCache构造函数的参数

    Returns:
        Cache实例
    """
    from .redis_cache import RedisCache

    return RedisCache(**kwargs)
