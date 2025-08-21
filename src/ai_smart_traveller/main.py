import time

from fastapi import Request

from .api.chat import router as chat_router
from .api.wechat import router as wechat_router
from .core.app_factory import app_factory
from .core.config import get_settings
from .core.logging import setup_logging

# 初始化配置
settings = get_settings()
# 设置日志
logger = setup_logging()

# 使用factory创建应用
app = app_factory.create_fastapi_app()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求访问日志"""
    start_time = time.time()

    # 获取请求信息
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    }

    # 处理请求
    response = await call_next(request)

    # 计算处理时间
    process_time = time.time() - start_time

    # 记录访问日志
    logger.info(
        f"Request processed in {process_time:.3f}s",
        extra={
            "request": request_info,
            "status_code": response.status_code,
            "process_time": process_time,
        },
    )

    return response


# 注册路由 - 只保留wechat和chat
app.include_router(wechat_router)
app.include_router(chat_router)
