"""
LLM工厂类 - 支持ChatGPT和阿里的通义千问
"""

import logging
from typing import Literal, Optional

from langchain_openai import ChatOpenAI

from .config import get_settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """LLM工厂类，支持ChatGPT和阿里的通义千问"""

    @staticmethod
    def create_llm(
        llm_type: Literal["qianwen", "gpt4", "gpt5"] = "gpt4",
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ):
        """
        创建LLM实例

        Args:
            llm_type: LLM类型，"qianwen"、"gpt4" 或 "gpt5"
            model_name: 模型名称，如果为None则使用默认值
            temperature: 温度参数，如果为None则使用默认值
            **kwargs: 其他参数

        Returns:
            LLM实例
        """
        try:
            logger.info(f"开始创建LLM，类型: {llm_type}")

            if llm_type == "qianwen":
                return LLMFactory._create_qianwen_llm(model_name, temperature, **kwargs)
            if llm_type == "gpt4":
                return LLMFactory._create_gpt4_llm(model_name, temperature, **kwargs)
            if llm_type == "gpt5":
                return LLMFactory._create_gpt5_llm(model_name, **kwargs)

        except Exception as e:
            logger.error(f"LLM创建失败，类型: {llm_type}, 错误: {e}")
            raise

    @staticmethod
    def _create_qianwen_llm(
        model_name: Optional[str] = None, temperature: Optional[float] = None, **kwargs
    ):
        """创建阿里的通义千问LLM实例"""
        try:
            settings = get_settings()

            if not settings.DASHSCOPE_API_KEY:
                error_msg = "通义千问API密钥未配置"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 设置dashscope API密钥
            import dashscope

            dashscope.api_key = settings.DASHSCOPE_API_KEY

            # 尝试使用ChatOpenAI作为替代方案，通过API代理
            from langchain_openai import ChatOpenAI

            # 使用通义千问的API端点
            llm = ChatOpenAI(
                model=model_name or settings.QIANWEN_MODEL_NAME,
                temperature=temperature or settings.QIANWEN_TEMPERATURE,
                openai_api_key=settings.DASHSCOPE_API_KEY,
                openai_api_base=settings.DASHSCOPE_API_BASE,
                **kwargs,
            )

            logger.info(
                f"通义千问LLM创建成功（使用兼容模式），模型: {model_name or settings.QIANWEN_MODEL_NAME}"
            )
            return llm
        except Exception as e:
            logger.error(f"通义千问LLM创建失败: {e}")
            raise

    @staticmethod
    def _create_gpt4_llm(
        model_name: Optional[str] = None, temperature: Optional[float] = None, **kwargs
    ) -> ChatOpenAI:
        """专用于 GPT-4 系列的创建逻辑（Functions Agent 友好）"""
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            error_msg = "OpenAI API密钥未配置"
            logger.error(error_msg)
            raise ValueError(error_msg)

        llm_kwargs = {
            "model_name": model_name or settings.OPENAI_MODEL_NAME,
            "openai_api_key": settings.OPENAI_API_KEY,
            "openai_api_base": settings.OPENAI_API_BASE,
            **kwargs,
        }
        # gpt-4 支持 temperature
        llm_kwargs["temperature"] = (
            temperature if temperature is not None else settings.OPENAI_TEMPERATURE
        )

        llm = ChatOpenAI(**llm_kwargs)
        logger.info(f"GPT-4 LLM创建成功，模型: {llm_kwargs['model_name']}")
        return llm

    @staticmethod
    def _create_gpt5_llm(model_name: Optional[str] = None, **kwargs) -> ChatOpenAI:
        """专用于 GPT-5 系列的创建逻辑（Tool Calling Agent 友好）"""
        settings = get_settings()

        # GPT-5 专用参数
        gpt5_kwargs = {
            "model_name": model_name or settings.OPENAI_GPT5_MODEL_NAME,
            "openai_api_key": settings.OPENAI_API_KEY,
            "openai_api_base": settings.OPENAI_API_BASE,
        }

        # 暂时移除 extra_body 参数，避免兼容性问题
        # extra_body = {
        #     "verbosity": "auto",  # 自动详细程度
        # }
        # gpt5_kwargs["extra_body"] = extra_body

        # 合并其他参数
        gpt5_kwargs.update(kwargs)

        llm = ChatOpenAI(**gpt5_kwargs)

        logger.info(f"GPT-5 LLM创建成功，模型: {gpt5_kwargs['model_name']}")
        return llm

    @staticmethod
    def get_default_llm_type() -> str:
        """获取默认LLM类型"""
        try:
            settings = get_settings()
            default_type = settings.DEFAULT_LLM_TYPE
            logger.debug(f"获取默认LLM类型: {default_type}")
            return default_type
        except Exception as e:
            logger.error(f"获取默认LLM类型失败: {e}")
            return "gpt4"  # 降级到默认值

    @staticmethod
    def create_default_llm(**kwargs):
        """创建默认LLM实例"""
        try:
            llm_type = LLMFactory.get_default_llm_type()
            logger.info(f"创建默认LLM，类型: {llm_type}")
            return LLMFactory.create_llm(llm_type, **kwargs)
        except Exception as e:
            logger.error(f"创建默认LLM失败: {e}")
            raise
