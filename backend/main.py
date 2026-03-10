"""
寻物记 - 后端 API 服务
FastAPI + SQLite + SQLAlchemy
"""
import time

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from models import init_db
from api import (
    auth_router, families_router, items_router,
    categories_router, reminders_router, chat_router, debug_router
)

# 创建应用
app = FastAPI(
    title="寻物记 API",
    description="家庭物品位置管理工具 - 存得明白，找得轻松",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册路由 (统一加 /api 前缀)
app.include_router(auth_router, prefix="/api")
app.include_router(families_router, prefix="/api")
app.include_router(items_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(debug_router, prefix="/api")


@app.middleware("http")
async def log_request_middleware(request, call_next):
    start = time.perf_counter()
    print(f"[http] -> {request.method} {request.url.path}?{request.url.query}")
    try:
        response = await call_next(request)
    except Exception as e:
        cost = int((time.perf_counter() - start) * 1000)
        print(f"[http] !! {request.method} {request.url.path} error={e} cost_ms={cost}")
        raise
    cost = int((time.perf_counter() - start) * 1000)
    print(f"[http] <- {request.method} {request.url.path} status={response.status_code} cost_ms={cost}")
    return response


@app.get("/", tags=["默认"])
def read_root():
    """根路径"""
    return {
        "message": "欢迎使用寻物记 API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health", tags=["默认"])
def health_check():
    """健康检查"""
    return {"status": "ok"}


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    init_db()
    print(f"✅ {settings.APP_NAME} API 启动成功")
    print(f"📖 API 文档: http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )