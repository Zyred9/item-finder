"""
寻物记 - 后端 API 服务
FastAPI + MySQL + SQLAlchemy
"""
import time

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.base import init_db
from config.settings import settings
from api import items, categories, reminders, chat, families, users, auth, debug, feedback

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="寻物记 - 帮你找东西",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（所有接口统一加 /api 前缀）
app.include_router(auth.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(families.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(debug.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")


# 定时任务：每天 00:00 刷新提醒
def _job_refresh_reminders():
    """每天凌晨刷新所有家庭的提醒"""
    from models.base import SessionLocal
    from services.expiry_reminder_agent import refresh_all_reminders

    db = SessionLocal()
    try:
        count = refresh_all_reminders(db)
        print(f"[Scheduler] Refreshed {count} reminders at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"[Scheduler] Error refreshing reminders: {e}")
    finally:
        db.close()


# 定时任务：每 30 秒同步搜索索引
def _job_sync_search_index():
    """每 30 秒同步搜索索引"""
    from models.base import SessionLocal
    from services.search_index_service import SearchIndexService

    db = SessionLocal()
    try:
        count = SearchIndexService.process_pending_tasks(db, limit=20)
        if count > 0:
            print(f"[Scheduler] Processed {count} search sync tasks at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"[Scheduler] Error syncing search index: {e}")
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
    print("[OK] Scheduled task registered: Daily 00:00 refresh reminders")
    print("[OK] Scheduled task registered: Every 30s sync search index")
    print(f"[OK] {settings.APP_NAME} API started successfully")
    print(f"[INFO] API Docs: http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
