import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI

from ..core.agent_builder import AgentBuilder
from ..core.agent_manager import AgentManager
from ..core.error_handler import http_exception_handler
from ..models.memory_manager import MemoryManager
from .config import get_settings

logger = logging.getLogger(__name__)


class AppFactory:
    """应用工厂类 - 直接使用AgentBuilder"""

    def __init__(self):
        self._memory_manager: Optional[MemoryManager] = None
        self._agent_builder: Optional[AgentBuilder] = None
        self._agent_manager: Optional[AgentManager] = None
        self._components: Dict[str, Any] = {}
        self.settings = get_settings()
        # 移除重复的日志初始化，由main.py统一管理

    def create_memory_manager(self) -> MemoryManager:
        """创建内存管理器"""
        if not self._memory_manager:
            self._memory_manager = MemoryManager(
                max_messages=self.settings.CHAT_MAX_MESSAGES,
                max_tokens=self.settings.CHAT_MAX_TOKENS,
                session_timeout_hours=self.settings.CHAT_SESSION_TIMEOUT_HOURS,
                cleanup_interval_hours=self.settings.CHAT_CLEANUP_INTERVAL_HOURS,
            )
            logger.info(
                f"创建内存管理器 - 最大消息数: {self.settings.CHAT_MAX_MESSAGES}, 最大token: {self.settings.CHAT_MAX_TOKENS}, 会话超时: {self.settings.CHAT_SESSION_TIMEOUT_HOURS}小时"
            )
        return self._memory_manager

    def create_agent_builder(self) -> AgentBuilder:
        """创建Agent构建器"""
        if not self._agent_builder:
            memory_manager = self.create_memory_manager()
            self._agent_builder = AgentBuilder(memory_manager)
            logger.info("已创建Agent构建器")
        return self._agent_builder

    def create_agent_manager(self) -> AgentManager:
        """创建Agent管理器"""
        if not self._agent_manager:
            memory_manager = self.create_memory_manager()
            self._agent_manager = AgentManager(memory_manager)
            logger.info("已创建Agent管理器")
        return self._agent_manager

    def get_component(self, name: str) -> Any:
        """获取组件"""
        return self._components.get(name)

    def register_component(self, name: str, component: Any):
        """注册自定义组件"""
        self._components[name] = component
        logger.info(f"注册自定义组件: {name}")

    def create_app(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建完整的应用实例"""
        config = config or {}

        # 创建核心组件
        memory_manager = self.create_memory_manager()
        agent_builder = self.create_agent_builder()
        agent_manager = self.create_agent_manager()

        return {
            "memory_manager": memory_manager,
            "agent_builder": agent_builder,
            "agent_manager": agent_manager,
            "components": self._components,
        }

    def reset(self):
        """重置所有组件"""
        self._memory_manager = None
        self._agent_builder = None
        self._agent_manager = None
        self._components.clear()
        logger.info("重置所有组件")

    def create_fastapi_app(self) -> FastAPI:
        """创建FastAPI应用"""
        app = FastAPI(
            title=self.settings.APP_NAME,
            version=self.settings.APP_VERSION,
            debug=self.settings.DEBUG,
        )

        # 注册全局异常处理器
        app.add_exception_handler(Exception, http_exception_handler)

        return app


# 全局应用工厂实例
app_factory = AppFactory()
