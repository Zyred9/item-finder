"""
清空所有表数据（无外键约束后可安全执行）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from config.settings import settings


def truncate_all():
    """清空所有表"""
    engine = create_engine(settings.DATABASE_URL)
    
    # 按正确顺序清空（避免自增 ID 冲突）
    tables = [
        "search_sync_tasks",
        "feedbacks",
        "chat_messages",
        "reminders",
        "item_extensions",
        "items",
        "users",
        "categories",
        "families",
    ]
    
    with engine.connect() as conn:
        # 禁用外键检查
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        for table in tables:
            try:
                conn.execute(text(f"TRUNCATE TABLE {table}"))
                print(f"[OK] Truncated: {table}")
            except Exception as e:
                print(f"[ERROR] {table}: {e}")
        
        # 恢复外键检查
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
    
    print("\n[DONE] All tables truncated!")


if __name__ == "__main__":
    print("[WARNING] This will DELETE ALL data from the database!")
    print("[INFO] Press Enter to continue or Ctrl+C to cancel")
    try:
        input()
        truncate_all()
    except KeyboardInterrupt:
        print("\n[CANCELLED]")
        sys.exit(1)
