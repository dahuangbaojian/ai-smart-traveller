import logging
from typing import Literal

from langchain.agents import (
    AgentExecutor,
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..core.prompts import get_chat_system_prompt
from ..models.memory_manager import MemoryManager
from .llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class AgentBuilder:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        logger.info("AgentBuilder初始化完成")

    def _get_tools(self):
        """获取可用工具列表"""
        try:
            from ..tools.travel_tools import get_travel_info, search_destinations

            # 将函数转换为LangChain工具格式
            from langchain.tools import Tool

            tools = [
                Tool(
                    name="get_travel_info",
                    description="获取指定旅游目的地的详细信息，包括景点、最佳时间、小贴士等。输入应该是目的地名称，如'北京'、'巴黎'等。",
                    func=get_travel_info,
                ),
                Tool(
                    name="search_destinations",
                    description="根据关键词搜索旅游目的地，支持按类别筛选。输入格式：关键词 类别，如'海岛'、'古城 美食'等。",
                    func=search_destinations,
                ),
            ]

            logger.info(f"加载了 {len(tools)} 个旅游工具")
            return tools

        except ImportError as e:
            logger.warning(f"无法导入旅游工具: {e}")
            return []
        except Exception as e:
            logger.error(f"加载工具失败: {e}")
            return []

    def _create_llm(self, llm_type: Literal["qianwen", "gpt4", "gpt5"] = "gpt4"):
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
        llm_type: Literal["qianwen", "gpt4", "gpt5"] = "gpt4",
        use_memory: bool = True,
    ):
        """
        构建智能旅游咨询Agent

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

            tools = self._get_tools()
            llm = self._create_llm(llm_type)

            # 如果没有工具，使用简单的对话模式
            if not tools:
                logger.info("没有可用工具，使用简单对话模式")
                return self._create_simple_chat_wrapper(llm, system_prompt, use_memory, user_id)

            # 根据模型类型选择不同的Agent创建方式
            model_name = getattr(llm, "model", "") or getattr(llm, "model_name", "")

            if model_name.startswith("gpt-5"):
                # GPT-5 使用 Tool Calling Agent
                agent = self._create_structured_agent(llm, tools, system_prompt, use_memory)
            else:
                # GPT-4 等其他模型使用 OpenAI Functions Agent
                agent = self._create_functions_agent(llm, tools, system_prompt, use_memory)

            # 创建 AgentExecutor
            executor_kwargs = {
                "agent": agent,
                "tools": tools,
                "verbose": True,
                "max_iterations": 8,
                "handle_parsing_errors": True,
                "return_intermediate_steps": True,
            }

            # 根据模型类型设置不同的执行时间限制
            if model_name.startswith("gpt-5"):
                executor_kwargs["max_execution_time"] = 90  # 3分钟
            else:
                executor_kwargs["max_execution_time"] = 60  # 1分钟
                executor_kwargs["stop"] = ["\nObservation:", "\n\tObservation:"]

            agent_executor = AgentExecutor(**executor_kwargs)

            if use_memory:
                # 对话式场景：需要上下文记忆
                memory = self.memory_manager.get_memory(user_id)
                result = self._create_memory_wrapper(agent_executor, memory)
                logger.info(f"对话式Agent构建成功，用户: {user_id}")
            else:
                # 任务式场景：不需要上下文记忆
                result = agent_executor
                logger.info(f"任务式Agent构建成功，用户: {user_id}")

            return result

        except Exception as e:
            logger.error(f"Agent构建失败，用户: {user_id}, 错误: {e}")
            raise

    def _create_functions_agent(self, llm, tools, system_prompt: str, use_memory: bool):
        """创建 OpenAI Functions Agent（用于 GPT-4 等模型）"""
        try:
            model_name = getattr(llm, "model", "") or getattr(llm, "model_name", "unknown")
            logger.info(f"创建 OpenAI Functions Agent，模型: {model_name}")
            from langchain.agents import create_openai_functions_agent

            agent = create_openai_functions_agent(
                llm, tools, self._create_prompt(system_prompt, use_memory)
            )
            return agent
        except Exception as e:
            logger.error(f"OpenAI Functions Agent 创建失败: {e}")
            raise

    def _create_structured_agent(self, llm, tools, system_prompt: str, use_memory: bool):
        """创建 Tool Calling Agent（用于 GPT-5 等模型）"""
        try:
            logger.info(f"创建 Tool Calling Agent，模型: {getattr(llm, 'model_name', 'unknown')}")
            from langchain.agents import create_tool_calling_agent

            agent = create_tool_calling_agent(
                llm,
                tools,
                self._create_structured_prompt(system_prompt, use_memory, tools),
            )
            return agent
        except Exception as e:
            logger.error(f"Structured Agent 创建失败: {e}")
            raise

    def _create_prompt(self, system_prompt: str, use_memory: bool):
        """创建prompt模板（用于OpenAI Functions Agent）"""
        try:
            if use_memory:
                # 包含历史消息的prompt
                prompt = ChatPromptTemplate.from_messages(
                    [
                        SystemMessage(content=system_prompt),
                        MessagesPlaceholder(variable_name="history"),
                        ("human", "{input}"),
                        MessagesPlaceholder(variable_name="agent_scratchpad"),
                    ]
                )
                logger.debug("创建包含历史消息的prompt模板")
            else:
                # 不包含历史消息的prompt
                prompt = ChatPromptTemplate.from_messages(
                    [
                        SystemMessage(content=system_prompt),
                        ("human", "{input}"),
                        MessagesPlaceholder(variable_name="agent_scratchpad"),
                    ]
                )
                logger.debug("创建不包含历史消息的prompt模板")

            return prompt

        except Exception as e:
            logger.error(f"Prompt模板创建失败: {e}")
            raise

    def _create_structured_prompt(self, system_prompt: str, use_memory: bool, tools):
        """创建 Tool Calling Agent 的 prompt 模板"""
        # 提取工具名称列表
        tool_names = [tool.name for tool in tools] if tools else []
        tool_names_str = "、".join(tool_names) if tool_names else "无可用工具"

        # 构建完整的系统提示词，包含工具信息
        tools_info = (
            "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
            if tools
            else "无可用工具"
        )
        system_rules = (
            f"{system_prompt}\n\n"
            "你可以使用下列工具来完成任务。\n"
            f"【可用工具】\n{tools_info}\n\n"
            f"当需要调用工具时，只能从以下工具名中选择：{tool_names_str}。\n"
            "如果已经具备足够信息或工具不可用，请直接回答，**不要重复调用工具**。"
        )

        # 对于 Structured Agent，使用简单的 prompt 格式
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_rules),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt

    def _create_memory_wrapper(self, agent_executor, memory):
        """创建带记忆的Agent包装器"""

        class AgentWrapper:
            def __init__(self, agent_executor, chat_history):
                self.agent_executor = agent_executor
                self.chat_history = chat_history
                logger.debug("AgentWrapper初始化完成")

            async def ainvoke(self, input_dict, config=None, **kwargs):
                try:
                    # 添加历史消息到输入
                    input_dict["history"] = self.chat_history.messages
                    logger.debug(f"处理用户输入，历史消息数量: {len(self.chat_history.messages)}")

                    result = await self.agent_executor.ainvoke(input_dict, config, **kwargs)

                    # 保存新的消息到历史
                    user_id = None
                    if config and hasattr(config, "get"):
                        user_id = config.get("user_id")
                    elif "user_id" in kwargs:
                        user_id = kwargs["user_id"]

                    if user_id and hasattr(self.chat_history, "add_message_with_limits"):
                        # 使用增强的记忆管理
                        self.chat_history.add_message_with_limits(
                            user_id, HumanMessage(content=input_dict["input"])
                        )
                        self.chat_history.add_message_with_limits(
                            user_id, AIMessage(content=result["output"])
                        )
                    else:
                        # 传统方式
                        self.chat_history.add_message(HumanMessage(content=input_dict["input"]))
                        self.chat_history.add_message(AIMessage(content=result["output"]))

                    # 检查是否需要显示限制警告
                    if hasattr(self.chat_history, "get_limit_warning"):
                        warning = self.chat_history.get_limit_warning()
                        if warning:
                            result["output"] = result["output"] + "\n\n" + warning
                            logger.info(f"向用户 {user_id} 显示限制警告")

                    logger.debug("消息已保存到历史记录")
                    return result

                except Exception as e:
                    logger.error(f"Agent调用失败: {e}")
                    raise

        return AgentWrapper(agent_executor, memory)

    def _create_simple_chat_wrapper(self, llm, system_prompt: str, use_memory: bool, user_id: str):
        """创建简单的对话包装器（用于没有工具的情况）"""
        try:
            logger.info(f"创建简单对话包装器，模型: {getattr(llm, 'model', 'unknown')}")

            class SimpleChatWrapper:
                def __init__(self, llm, system_prompt: str, use_memory: bool, user_id: str):
                    self.llm = llm
                    self.system_prompt = system_prompt
                    self.use_memory = use_memory
                    self.user_id = user_id
                    self.memory_manager = self.memory_manager if use_memory else None
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
                        response_text = self._extract_response_text(response)

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
                        response_text = self._extract_response_text(response)

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

                def _extract_response_text(self, response):
                    """从LLM响应中提取纯文本内容"""
                    try:
                        if hasattr(response, "content"):
                            return response.content
                        elif hasattr(response, "text"):
                            return response.text
                        elif isinstance(response, str):
                            return response
                        else:
                            return str(response)
                    except Exception:
                        return str(response)

            return SimpleChatWrapper(llm, system_prompt, use_memory, user_id)

        except Exception as e:
            logger.error(f"简单对话包装器创建失败: {e}")
            raise
