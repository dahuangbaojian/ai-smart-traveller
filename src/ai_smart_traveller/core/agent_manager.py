"""
Agent管理器 - 实现Agent的复用和缓存
"""

import logging
import time
from typing import Dict, Literal, Optional

from ..models.memory_manager import MemoryManager
from .agent_builder import AgentBuilder
from .prompts import KEYWORD_EXTRACT_SYSTEM_PROMPT, get_chat_system_prompt

logger = logging.getLogger(__name__)


class AgentManager:
    """Agent管理器，负责Agent的创建、缓存和复用"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.agent_builder = AgentBuilder(memory_manager)

        # Agent缓存：按用户ID和类型缓存
        self._agent_cache: Dict[str, object] = {}
        self._cache_timestamps: Dict[str, float] = {}  # 缓存时间戳

        # 缓存配置
        self._max_cache_size = 100  # 最大缓存数量
        self._cache_ttl = 900  # 缓存TTL（秒）- 15分钟

        # 启动自动清理任务
        self._start_cleanup_task()

        logger.info("AgentManager初始化完成")

    def get_chat_agent(
        self, user_id: str, llm_type: Optional[Literal["qianwen", "gpt4", "gpt5"]] = None
    ):
        """
        获取对话式Agent（有记忆）

        Args:
            user_id: 用户ID
            llm_type: LLM类型

        Returns:
            Agent实例
        """
        # 如果没有指定 llm_type，使用默认配置
        if llm_type is None:
            from .llm_factory import LLMFactory

            llm_type = LLMFactory.get_default_llm_type()

        cache_key = f"chat_{user_id}_{llm_type}"

        # 检查缓存
        if cache_key in self._agent_cache:
            logger.debug(f"使用缓存的对话Agent，用户: {user_id}")
            return self._agent_cache[cache_key]

        # 创建新的Agent
        logger.info(f"创建新的对话Agent，用户: {user_id}, LLM类型: {llm_type}")
        agent = self.agent_builder.build_agent(
            user_id=user_id,
            system_prompt=get_chat_system_prompt(),
            llm_type=llm_type,
            use_memory=True,
        )

        # 缓存Agent
        self._cache_agent(cache_key, agent)

        return agent

    def get_task_agent(
        self, task_id: str, llm_type: Optional[Literal["qianwen", "gpt4", "gpt5"]] = None
    ):
        """
        获取任务式Agent（无记忆）

        Args:
            task_id: 任务ID
            llm_type: LLM类型

        Returns:
            Agent实例
        """
        # 如果没有指定 llm_type，使用默认配置
        if llm_type is None:
            from .llm_factory import LLMFactory

            llm_type = LLMFactory.get_default_llm_type()

        cache_key = f"task_{task_id}_{llm_type}"

        # 检查缓存
        if cache_key in self._agent_cache:
            logger.debug(f"使用缓存的任务Agent，任务: {task_id}")
            return self._agent_cache[cache_key]

        # 创建新的Agent
        logger.info(f"创建新的任务Agent，任务: {task_id}, LLM类型: {llm_type}")
        agent = self.agent_builder.build_agent(
            user_id=task_id,
            system_prompt=KEYWORD_EXTRACT_SYSTEM_PROMPT,
            llm_type=llm_type,
            use_memory=False,
        )

        # 缓存Agent
        self._cache_agent(cache_key, agent)

        return agent

    def _cache_agent(self, cache_key: str, agent: object):
        """缓存Agent"""
        # 检查缓存大小
        if len(self._agent_cache) >= self._max_cache_size:
            # 简单的LRU策略：删除第一个
            first_key = next(iter(self._agent_cache))
            del self._agent_cache[first_key]
            if first_key in self._cache_timestamps:
                del self._cache_timestamps[first_key]
            logger.debug(f"缓存已满，删除Agent: {first_key}")

        # 添加新Agent
        self._agent_cache[cache_key] = agent
        self._cache_timestamps[cache_key] = time.time()
        logger.debug(f"缓存Agent: {cache_key}")

    def _start_cleanup_task(self):
        """启动自动清理任务"""
        import threading

        def cleanup_loop():
            """清理循环"""
            while True:
                try:
                    self._cleanup_expired_cache()
                    # 每5分钟清理一次
                    time.sleep(300)
                except Exception as e:
                    logger.error(f"自动清理任务异常: {e}")
                    time.sleep(60)  # 异常时等待1分钟再重试

        # 在后台线程中运行清理任务
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Agent缓存自动清理任务已启动")

    def _cleanup_expired_cache(self):
        """清理过期的缓存"""
        current_time = time.time()
        expired_keys = []

        for cache_key, cache_time in self._cache_timestamps.items():
            if (current_time - cache_time) >= self._cache_ttl:
                expired_keys.append(cache_key)

        if expired_keys:
            for key in expired_keys:
                del self._agent_cache[key]
                del self._cache_timestamps[key]
            logger.info(f"自动清理过期Agent缓存，共{len(expired_keys)}个")
        else:
            logger.debug("没有过期的Agent缓存需要清理")

    def clear_user_agent(self, user_id: str):
        """清除用户的Agent缓存"""
        keys_to_remove = []
        for key in self._agent_cache.keys():
            if key.startswith(f"chat_{user_id}_"):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._agent_cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]
            logger.info(f"清除用户Agent缓存: {key}")

    def clear_all_cache(self):
        """清除所有Agent缓存"""
        cache_size = len(self._agent_cache)
        self._agent_cache.clear()
        self._cache_timestamps.clear()
        logger.info(f"清除所有Agent缓存，共{cache_size}个")

    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        chat_agents = sum(1 for key in self._agent_cache.keys() if key.startswith("chat_"))
        task_agents = sum(1 for key in self._agent_cache.keys() if key.startswith("task_"))

        return {
            "total_agents": len(self._agent_cache),
            "chat_agents": chat_agents,
            "task_agents": task_agents,
            "max_cache_size": self._max_cache_size,
        }
