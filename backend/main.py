"""
寻物记 - 后端 API 服务
FastAPI + SQLite + SQLAlchemy
"""
import time

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from models.base import SessionLocal
from services import ReminderService
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from tasks.search_sync_worker import run_once as run_search_sync_once

from config.settings import settings
from models import init_db
from api import (
    auth_router,
    families_router,
    items_router,
    categories_router,
    reminders_router,
    chat_router,
    debug_router,
    users_router,
    feedback_router,
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
app.include_router(users_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")


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


def _job_refresh_reminders():
    """每日 00:00 执行：刷新待处理提醒的剩余天数、标题、级别、内容"""
    db = SessionLocal()
    try:
        n = ReminderService.refresh_pending_reminders(db)
        if n > 0:
            print(f"[cron] 已刷新 {n} 条智能提醒")
    except Exception as e:
        print(f"[cron] 刷新智能提醒失败: {e}")
    finally:
        db.close()


def _job_sync_search_index():
    """定时补偿 MySQL -> Qdrant 的失败同步任务"""
    db = SessionLocal()
    try:
        count = run_search_sync_once(db=db, limit=20)
        if count > 0:
            print(f"[cron] 已处理 {count} 条搜索索引同步任务")
    except Exception as err:
        print(f"[cron] 搜索索引补偿失败: {err}")
    finally:
        db.close()


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(_job_refresh_reminders, "cron", hour=0, minute=0)
    scheduler.add_job(_job_sync_search_index, "interval", seconds=30)
    scheduler.start()
    print("✅ 定时任务已注册：每日 00:00 刷新智能提醒")
    print("✅ 定时任务已注册：每 30 秒补偿搜索索引任务")
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