import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def log_tool_calls(response: Dict[str, Any], user_id: str = "system"):
    """记录工具调用信息"""
    if "intermediate_steps" in response:
        for step in response["intermediate_steps"]:
            if len(step) >= 2:
                action, observation = step[0], step[1]
                logger.debug(
                    f"工具调用: {action.tool} - 参数: {action.tool_input}",
                    extra={"user_id": user_id},
                )
                logger.info(f"工具返回: {observation}", extra={"user_id": user_id})
    else:
        logger.debug("未检测到工具调用", extra={"user_id": user_id})
