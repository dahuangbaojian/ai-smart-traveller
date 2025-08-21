#!/usr/bin/env python3
"""
AI智能旅游咨询专家系统启动脚本
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_smart_traveller.core.config import get_settings
from src.ai_smart_traveller.core.logging import setup_logging


def main():
    """主函数"""
    try:
        # 设置日志
        logger = setup_logging()
        logger.info("🚀 启动AI智能旅游咨询专家系统...")

        # 获取配置
        settings = get_settings()

        # 检查必要的配置
        if not settings.OPENAI_API_KEY and not settings.DASHSCOPE_API_KEY:
            logger.error("❌ 未配置任何LLM API密钥，请检查配置文件")
            sys.exit(1)

        # 显示配置信息
        logger.info(f"📋 应用名称: {settings.APP_NAME}")
        logger.info(f"📋 应用版本: {settings.APP_VERSION}")
        logger.info(f"📋 服务地址: {settings.HOST}:{settings.PORT}")
        logger.info(f"📋 工作进程数: {settings.WORKERS}")
        logger.info(f"📋 调试模式: {settings.DEBUG}")
        logger.info(f"📋 默认LLM: {settings.DEFAULT_LLM_TYPE}")

        # 检查LLM配置
        if settings.OPENAI_API_KEY:
            if settings.OPENAI_API_BASE:
                logger.info("✅ OpenAI配置正常（使用代理）")
            else:
                logger.info("✅ OpenAI配置正常（直连）")
        else:
            logger.warning("⚠️ OpenAI未配置")

        if settings.DASHSCOPE_API_KEY:
            logger.info("✅ 通义千问配置正常")
        else:
            logger.warning("⚠️ 通义千问未配置")

        # 启动服务器
        logger.info("🌐 启动Web服务器...")
        uvicorn.run(
            "src.ai_smart_traveller.main:app",
            host=settings.HOST,
            port=settings.PORT,
            workers=settings.WORKERS,
            reload=settings.DEBUG,
            log_level="info" if not settings.DEBUG else "debug",
            access_log=True,
        )

    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
