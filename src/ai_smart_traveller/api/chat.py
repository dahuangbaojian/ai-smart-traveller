import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ..core.app_factory import app_factory
from ..core.error_handler import error_handler
from ..utils.logging_utils import log_tool_calls
from ..utils.text_to_pdf import text_to_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天"])

# 使用工厂创建应用组件
app_components = app_factory.create_app()
agent_manager = app_components["agent_manager"]
memory_manager = app_components["memory_manager"]


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    error_message: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
@error_handler("聊天处理")
async def chat(request: ChatRequest, x_user_id: str = Header(..., description="用户ID")):
    """
    智能旅游咨询聊天接口

    Args:
        request: 聊天请求，包含用户问题
        x_user_id: 用户ID，用于标识用户和保存对话历史

    Returns:
        ChatResponse: 包含AI回复的响应
    """
    try:
        logger.info(f"收到用户问题: {request.question}", extra={"user_id": x_user_id})

        # 验证用户ID
        if not x_user_id or len(x_user_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="用户ID不能为空")

        # 验证问题内容
        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(status_code=400, detail="问题内容不能为空")

        # 使用AgentManager获取或创建Agent（支持复用）
        agent = agent_manager.get_chat_agent(user_id=x_user_id)
        response = await agent.ainvoke({"input": request.question}, config={"user_id": x_user_id})

        # 记录工具调用信息
        log_tool_calls(response, x_user_id)

        logger.debug(f"Agent返回结果: {response}", extra={"user_id": x_user_id})
        logger.info(f"返回用户回答: {response.get('output', '')}", extra={"user_id": x_user_id})

        # 从output字段获取响应内容
        response_text = response.get("output", "处理失败")
        # 确保是字符串
        if not isinstance(response_text, str):
            response_text = str(response_text)

        # 生成PDF文件用于保存和分享
        try:
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_prefix = f"travel_consultation_{timestamp}"

            # 生成PDF文件
            pdf_path = text_to_pdf(response_text, filename_prefix=filename_prefix)

            if pdf_path:
                logger.info(f"已生成PDF文件: {pdf_path}", extra={"user_id": x_user_id})
            else:
                logger.warning("PDF文件生成失败", extra={"user_id": x_user_id})

        except Exception as e:
            logger.error(f"生成PDF文件失败: {e}", extra={"user_id": x_user_id})

        # 接口返回原始的response_text，PDF文件已保存用于分享
        return ChatResponse(response=response_text, success=True)

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"聊天处理失败，用户: {x_user_id}, 错误: {e}", extra={"user_id": x_user_id})
        return ChatResponse(
            response="抱歉，处理您的问题时出现了错误，请稍后重试。",
            success=False,
            error_message=str(e),
        )
