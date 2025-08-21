import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


class LimitedChatMessageHistory(InMemoryChatMessageHistory):
    """带限制功能的聊天消息历史"""

    def __init__(
        self, memory_manager, user_id: str, max_messages: int = 20, max_tokens: int = 4000
    ):
        super().__init__()
        # 使用私有属性避免与Pydantic冲突
        self._memory_manager = memory_manager
        self._user_id = user_id
        self._max_messages = max_messages
        self._max_tokens = max_tokens

    def add_message(self, message: BaseMessage) -> None:
        """添加消息并应用限制"""
        super().add_message(message)
        self._apply_limits()

    def get_limit_warning(self) -> Optional[str]:
        """获取限制警告信息"""
        messages = self.messages
        message_count = len(messages)

        warnings = []

        # 消息数量警告
        if message_count >= self._max_messages * 0.8:
            warnings.append(f"对话消息数量({message_count}/{self._max_messages})")

        # Token数量警告
        estimated_tokens = self._estimate_tokens(messages)
        if estimated_tokens >= self._max_tokens * 0.8:
            warnings.append(f"Token使用量({estimated_tokens}/{self._max_tokens})")

        if warnings:
            # 暂时关闭警告提示
            return None

        return None

    def add_message_with_limits(self, user_id: str, message: BaseMessage) -> None:
        """添加消息并应用限制（兼容方法）"""
        self.add_message(message)

    def _apply_limits(self) -> None:
        """应用消息和token限制"""
        messages = self.messages

        # 1. 消息数量限制
        if len(messages) > self._max_messages:
            # 保留最新的消息，删除最旧的
            excess_count = len(messages) - self._max_messages
            # 删除最旧的消息（保留系统消息）
            messages_to_remove = []
            for i, msg in enumerate(messages):
                if len(messages_to_remove) < excess_count and not self._is_system_message(msg):
                    messages_to_remove.append(i)

            # 从后往前删除，避免索引变化
            for i in reversed(messages_to_remove):
                del messages[i]

            logger.info(f"用户 {self._user_id} 消息数量超限，删除了 {excess_count} 条旧消息")

        # 2. Token数量限制（估算）
        estimated_tokens = self._estimate_tokens(messages)
        if estimated_tokens > self._max_tokens:
            # 删除最旧的消息直到token数量在限制内
            while estimated_tokens > self._max_tokens and len(messages) > 2:  # 保留至少2条消息
                # 找到最旧的非系统消息
                oldest_non_system_idx = None
                for i, msg in enumerate(messages):
                    if not self._is_system_message(msg):
                        oldest_non_system_idx = i
                        break

                if oldest_non_system_idx is not None:
                    del messages[oldest_non_system_idx]
                    estimated_tokens = self._estimate_tokens(messages)
                    logger.debug(
                        f"用户 {self._user_id} token超限，删除旧消息，当前估算token: {estimated_tokens}"
                    )
                else:
                    break

    def _estimate_tokens(self, messages: List[BaseMessage]) -> int:
        """估算消息的token数量（简单估算）"""
        total_tokens = 0
        for message in messages:
            # 简单估算：每个字符约0.75个token
            content = message.content if hasattr(message, "content") else str(message)
            total_tokens += int(len(content) * 0.75)
        return total_tokens

    def _is_system_message(self, message: BaseMessage) -> bool:
        """判断是否为系统消息"""
        return hasattr(message, "type") and message.type == "system"


class TimedMemoryManager:
    """带时间控制和token限制的记忆管理器"""

    def __init__(
        self,
        max_messages: int = 20,  # 最大消息数量
        max_tokens: int = 4000,  # 最大token数量（估算）
        session_timeout_hours: int = 24,  # 会话超时时间（小时）
        cleanup_interval_hours: int = 1,  # 清理间隔（小时）
    ):
        self._memories: Dict[str, BaseChatMessageHistory] = {}
        self._session_timestamps: Dict[str, datetime] = {}  # 记录每个用户的最后活跃时间
        self._max_messages = max_messages
        self._max_tokens = max_tokens
        self._session_timeout = timedelta(hours=session_timeout_hours)
        self._cleanup_interval = timedelta(hours=cleanup_interval_hours)
        self._last_cleanup = datetime.now()

        logger.info(
            f"TimedMemoryManager初始化完成 - 最大消息数: {max_messages}, 最大token: {max_tokens}, 会话超时: {session_timeout_hours}小时"
        )

    def get_memory(self, user_id: str) -> BaseChatMessageHistory:
        """获取用户记忆，如果不存在则创建新的"""
        current_time = datetime.now()

        # 定期清理过期会话
        self._cleanup_expired_sessions(current_time)

        if user_id not in self._memories:
            # 使用增强的聊天历史类
            self._memories[user_id] = LimitedChatMessageHistory(
                self, user_id, self._max_messages, self._max_tokens
            )
            self._session_timestamps[user_id] = current_time
            logger.info(f"为用户 {user_id} 创建新的记忆会话")
        else:
            # 更新最后活跃时间
            self._session_timestamps[user_id] = current_time

        return self._memories[user_id]

    def add_message(self, user_id: str, message: BaseMessage) -> None:
        """添加消息到用户记忆，并应用限制策略"""
        if user_id not in self._memories:
            self.get_memory(user_id)

        memory = self._memories[user_id]
        memory.add_message(message)

        # 更新活跃时间
        self._session_timestamps[user_id] = datetime.now()

    def clear_memory(self, user_id: str) -> None:
        """清除用户记忆"""
        if user_id in self._memories:
            del self._memories[user_id]
        if user_id in self._session_timestamps:
            del self._session_timestamps[user_id]
        logger.info(f"清除用户 {user_id} 的记忆")

    def get_session_info(self, user_id: str) -> Dict:
        """获取会话信息"""
        if user_id not in self._memories:
            return {"exists": False}

        memory = self._memories[user_id]
        last_active = self._session_timestamps.get(user_id)

        return {
            "exists": True,
            "message_count": len(memory.messages),
            "last_active": last_active.isoformat() if last_active else None,
            "session_age_hours": (
                (datetime.now() - last_active).total_seconds() / 3600 if last_active else 0
            ),
        }

    def _cleanup_expired_sessions(self, current_time: datetime) -> None:
        """清理过期的会话"""
        # 检查是否需要清理
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        expired_users = []
        for user_id, last_active in self._session_timestamps.items():
            if current_time - last_active > self._session_timeout:
                expired_users.append(user_id)

        # 清理过期会话
        for user_id in expired_users:
            self.clear_memory(user_id)
            logger.info(f"清理过期会话，用户: {user_id}")

        if expired_users:
            logger.info(f"清理了 {len(expired_users)} 个过期会话")

        self._last_cleanup = current_time


# 为了保持向后兼容，保留原来的类名
class MemoryManager(TimedMemoryManager):
    """向后兼容的MemoryManager类"""

    pass
