import logging
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..core.prompts import get_chat_system_prompt
from ..models.memory_manager import MemoryManager
from .llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class AgentBuilder:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        logger.info("AgentBuilder初始化完成")

    def _create_llm(self, llm_type: Literal["qianwen", "gpt4", "gpt5", "ollama"] = "gpt4"):
        """创建LLM实例"""
        try:
            llm = LLMFactory.create_llm(llm_type)
            logger.info(f"LLM创建成功，类型: {llm_type}")
            return llm
        except Exception as e:
            logger.error(f"LLM创建失败，类型: {llm_type}, 错误: {e}")
            raise

    def build_agent(
        self,
        user_id: str,
        system_prompt: str,
        llm_type: Literal["qianwen", "gpt4", "gpt5", "ollama"] = "gpt4",
        use_memory: bool = True,
    ):
        """
        构建简单的旅游咨询Agent

        Args:
            user_id: 用户ID
            system_prompt: 系统提示词
            llm_type: LLM类型
            use_memory: 是否使用上下文记忆，默认True
        """
        try:
            logger.info(
                f"开始构建旅游咨询Agent，用户: {user_id}, LLM类型: {llm_type}, 使用记忆: {use_memory}"
            )

            # 如果系统提示词为空，则使用动态获取的提示词
            if not system_prompt:
                system_prompt = get_chat_system_prompt()

            llm = self._create_llm(llm_type)

            # 创建简单的对话包装器
            return self._create_simple_chat_wrapper(llm, system_prompt, use_memory, user_id)

        except Exception as e:
            logger.error(f"Agent构建失败，用户: {user_id}, 错误: {e}")
            raise

    def _create_simple_chat_wrapper(
        self, llm, system_prompt: str, use_memory: bool, user_id: str
    ):
        """创建简单的对话包装器，直接使用LLM进行旅游咨询"""
        try:
            logger.info(f"创建简单对话包装器，模型: {getattr(llm, 'model', 'unknown')}")

            class SimpleChatWrapper:
                def __init__(self, llm, system_prompt: str, use_memory: bool, user_id: str):
                    self.llm = llm
                    self.system_prompt = system_prompt
                    self.use_memory = use_memory
                    self.user_id = user_id
                    self.memory_manager = None
                    if use_memory:
                        self.memory_manager = MemoryManager()
                    logger.debug("SimpleChatWrapper 初始化完成")

                async def ainvoke(self, input_dict, config=None, **kwargs):
                    try:
                        # 构建完整的 prompt
                        user_input = input_dict.get("input", "")

                        # 如果有记忆，添加历史消息
                        if self.use_memory and self.memory_manager:
                            memory = self.memory_manager.get_memory(self.user_id)
                            history_messages = memory.messages if memory else []
                            history_text = "\n".join(
                                [
                                    f"{'用户' if msg.type == 'human' else '助手'}: {msg.content}"
                                    for msg in history_messages
                                ]
                            )
                            if history_text:
                                full_prompt = f"{self.system_prompt}\n\n对话历史:\n{history_text}\n\n用户: {user_input}\n\n助手:"
                            else:
                                full_prompt = f"{self.system_prompt}\n\n用户: {user_input}\n\n助手:"
                        else:
                            full_prompt = f"{self.system_prompt}\n\n用户: {user_input}\n\n助手:"

                        # 调用 LLM
                        response = await self.llm.ainvoke(full_prompt)
                        response_text = str(response)

                        # 如果有记忆，保存对话
                        if self.use_memory and self.memory_manager:
                            memory = self.memory_manager.get_memory(self.user_id)
                            memory.add_message(HumanMessage(content=user_input))
                            memory.add_message(AIMessage(content=response_text))

                        # 返回标准格式
                        return {"output": response_text}

                    except Exception as e:
                        logger.error(f"SimpleChatWrapper 调用失败: {e}")
                        raise

                def invoke(self, input_dict, config=None, **kwargs):
                    try:
                        # 构建完整的 prompt
                        user_input = input_dict.get("input", "")

                        # 如果有记忆，添加历史消息
                        if self.use_memory and self.memory_manager:
                            memory = self.memory_manager.get_memory(self.user_id)
                            history_messages = memory.messages if memory else []
                            history_text = "\n".join(
                                [
                                    f"{'用户' if msg.type == 'human' else '助手'}: {msg.content}"
                                    for msg in history_messages
                                ]
                            )
                            if history_text:
                                full_prompt = f"{self.system_prompt}\n\n对话历史:\n{history_text}\n\n用户: {user_input}\n\n助手:"
                            else:
                                full_prompt = f"{self.system_prompt}\n\n用户: {user_input}\n\n助手:"
                        else:
                            full_prompt = f"{self.system_prompt}\n\n用户: {user_input}\n\n助手:"

                        # 调用 LLM
                        response = self.llm.invoke(full_prompt)
                        response_text = str(response)

                        # 如果有记忆，保存对话
                        if self.use_memory and self.memory_manager:
                            memory = self.memory_manager.get_memory(self.user_id)
                            memory.add_message(HumanMessage(content=user_input))
                            memory.add_message(AIMessage(content=response_text))

                        # 返回标准格式
                        return {"output": response_text}

                    except Exception as e:
                        logger.error(f"SimpleChatWrapper 调用失败: {e}")
                        raise

            return SimpleChatWrapper(llm, system_prompt, use_memory, user_id)

        except Exception as e:
            logger.error(f"简单对话包装器创建失败: {e}")
            raise
