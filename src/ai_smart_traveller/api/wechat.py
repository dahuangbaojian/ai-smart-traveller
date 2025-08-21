import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, Request, Response

from ..core.app_factory import app_factory
from ..core.error_handler import error_handler
from ..utils.logging_utils import log_tool_calls
from ..utils.wecom import WeComService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wechat", tags=["微信"])

# 使用工厂创建应用组件
app_components = app_factory.create_app()
agent_manager = app_components["agent_manager"]
memory_manager = app_components["memory_manager"]

# 创建微信服务单例
wecom_service = WeComService()


@router.post("/callback")
@error_handler("微信回调处理")
async def handle_callback(request: Request):
    """
    处理微信回调消息

    Args:
        request: FastAPI请求对象

    Returns:
        微信响应
    """
    try:
        # 获取请求体
        body = await request.body()

        # 获取URL参数
        query_params = dict(request.query_params)
        msg_signature = query_params.get("msg_signature", "")
        timestamp = query_params.get("timestamp", "")
        nonce = query_params.get("timestamp", "")

        logger.debug(
            f"微信回调参数: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}"
        )

        # 立即返回成功响应，避免微信重复推送
        # 异步处理消息，不阻塞响应
        asyncio.create_task(_process_message_async(body, msg_signature, timestamp, nonce))

        return Response(content="success", media_type="text/plain")

    except Exception as e:
        logger.error(f"微信回调处理失败: {e}")
        return Response(content="success", media_type="text/plain")


async def _process_message_async(body: bytes, msg_signature: str, timestamp: str, nonce: str):
    """异步处理微信消息"""
    try:
        # 解析微信消息
        message = wecom_service.parse_message(body, msg_signature, timestamp, nonce)

        if not message:
            logger.warning("无法解析微信消息")
            return

        # 获取用户详细信息（只获取一次，传递给所有处理器）
        user_id = message.get("from_user")
        user_info = _get_user_display_info(user_id)
        msg_type = message.get("msg_type")

        # 根据消息类型获取合适的内容描述
        if msg_type == "voice":
            message_content = f"语音消息 (格式: {message.get('voice_format', 'unknown')})"
        elif msg_type == "image":
            message_content = "图片消息"
        elif msg_type == "location":
            message_content = "位置消息"
        elif msg_type == "event":
            message_content = f"事件消息 ({message.get('event', 'unknown')})"
        else:
            message_content = message.get("content", "未知消息")

        logger.info(
            f"收到微信用户问题: {message_content} - 用户: {user_info['display_text']} - 消息类型: {msg_type}",
            extra={"user_id": user_info["user_name"]},
        )

        # 消息类型处理器映射
        message_handlers = {
            "text": _handle_text_message,
            "voice": _handle_voice_message,  # 语音消息处理
            "event": _handle_event_message,
        }

        # 获取对应的处理器
        handler = message_handlers.get(msg_type)
        if handler:
            await handler(message, user_info)
        else:
            logger.warning(f"暂不支持的消息类型: {msg_type}")
            await wecom_service.send_markdown_message(
                user_id, "❌ 暂不支持此类型消息，请发送文字消息"
            )

    except Exception as e:
        logger.error(f"处理微信消息失败: {e}")
        # 发送错误提示给用户
        try:
            user_id = message.get("from_user") if 'message' in locals() else "unknown"
            await wecom_service.send_markdown_message(user_id, "❌ 消息处理失败，请重试")
        except:
            pass


async def _handle_text_message(message: dict, user_info: dict = None):
    """处理文本消息"""
    try:
        user_id = message.get("from_user")
        content = message.get("content", "").strip()

        if not content:
            logger.warning("收到空文本消息", extra={"user_id": user_id})
            return

        logger.info(
            f"处理文本消息: {content}",
            extra={"user_id": user_info["user_name"]},
        )

        # 直接使用Agent处理文本内容
        await _process_ai_request(user_id, user_info["user_name"], content)

        logger.debug("文本消息处理完成", extra={"user_id": user_info["user_name"]})

    except Exception as e:
        logger.error(f"处理文本消息失败: {e}", extra={"user_id": message.get("from_user")})
        await wecom_service.send_markdown_message(
            message.get("from_user"), "❌ 文本消息处理失败，请重试"
        )


async def _handle_voice_message(message: dict, user_info: dict = None):
    """处理语音消息"""
    try:
        user_id = message.get("from_user")
        voice_url = message.get("voice_url", "")
        voice_format = message.get("voice_format", "amr")

        if not voice_url:
            logger.warning("收到空语音消息", extra={"user_id": user_id})
            return

        logger.info(
            f"处理语音消息: {voice_url}, 格式: {voice_format}",
            extra={"user_id": user_info["user_name"]},
        )

        # 简化语音处理：直接提示用户发送文字
        await wecom_service.send_markdown_message(
            user_id, "🎤 语音消息功能暂未开放，请发送文字消息进行旅游咨询"
        )

        logger.debug("语音消息处理完成", extra={"user_id": user_info["user_name"]})

    except Exception as e:
        logger.error(f"处理语音消息失败: {e}", extra={"user_id": message.get("from_user")})
        await wecom_service.send_markdown_message(
            message.get("from_user"), "❌ 语音消息处理失败，请重试"
        )


async def _process_ai_request(user_id: str, user_name: str, content: str):
    """公共的AI请求处理逻辑"""
    try:
        # 使用AgentManager获取或创建Agent（支持复用）
        agent = agent_manager.get_chat_agent(user_id=user_id)
        response = await agent.ainvoke({"input": content})

        # 记录工具调用信息
        log_tool_calls(response, user_name)

        # 获取AI回复
        ai_response = response.get("output", "处理失败")
        if not isinstance(ai_response, str):
            ai_response = str(ai_response)

        logger.info(f"AI回复: {ai_response}", extra={"user_id": user_name})

        # 发送回复到微信（使用markdown格式支持颜色标签）
        await wecom_service.send_markdown_message(user_id, ai_response)

    except Exception as e:
        logger.error(f"AI请求处理失败: {e}", extra={"user_id": user_name})
        # 发送错误提示给用户
        error_message = "❌ AI处理失败，请重试或联系管理员"
        await wecom_service.send_markdown_message(user_id, error_message)


async def _handle_event_message(message: dict, user_info: dict = None):
    """处理事件消息"""
    try:
        user_id = message.get("from_user")
        event = message.get("event")

        logger.info(f"处理事件消息: {event}", extra={"user_id": user_id})

        if event == "subscribe":
            # 订阅事件 - 发送欢迎消息
            welcome_message = """🎉 你好，我是AI智能旅游咨询专家！

🌟 我可以帮你：
• 推荐旅游目的地
• 制定旅游行程
• 介绍景点特色
• 推荐酒店美食
• 提供交通建议
• 解答旅游疑问

请告诉我你的旅游需求，我会为你提供专业的建议！"""

            await wecom_service.send_markdown_message(user_id, welcome_message)
            logger.info("发送订阅欢迎消息完成", extra={"user_id": user_id})

        elif event == "unsubscribe":
            # 取消订阅事件
            logger.info("用户取消订阅", extra={"user_id": user_id})

        else:
            # 其他事件类型
            logger.info(f"暂不支持的事件类型: {event}", extra={"user_id": user_id})

    except Exception as e:
        logger.error(f"处理事件消息失败: {e}", extra={"user_id": message.get("from_user")})


def _get_user_display_info(user_id: str) -> Dict[str, Any]:
    """获取用户显示信息（姓名+部门）"""
    try:
        user_info = wecom_service.get_user_info(user_id)

        if user_info.get("errcode") == 0:
            user_name = user_info.get("name", "未知用户")
            user_departments = user_info.get("department", [])

            # 获取部门名称
            department_names = []
            for dept_id in user_departments:
                dept_info = wecom_service.get_department_info(dept_id)
                if dept_info.get("errcode") == 0:
                    dept_name = dept_info.get("name", "未知部门")
                    department_names.append(dept_name)

            # 构建显示文本
            if department_names:
                display_text = f"{user_name} ({', '.join(department_names)})"
            else:
                display_text = user_name

            return {
                "user_name": user_name,
                "department_names": department_names,
                "display_text": display_text,
            }
        else:
            # 获取用户信息失败，使用默认值
            logger.warning(f"获取用户信息失败: {user_info.get('errmsg', 'unknown error')}")
            return {
                "user_name": f"用户{user_id}",
                "department_names": [],
                "display_text": f"用户{user_id}",
            }

    except Exception as e:
        logger.error(f"获取用户显示信息失败: {e}")
        # 返回默认值
        return {
            "user_name": f"用户{user_id}",
            "department_names": [],
            "display_text": f"用户{user_id}",
        }
