"""
移除所有外键约束脚本
自动运行，无需交互
"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from config.settings import settings


def remove_foreign_keys():
    """移除所有外键约束"""
    engine = create_engine(settings.DATABASE_URL)
    
    # 需要清理的表和外键约束名（MySQL 外键命名规则：表名_列名_fkey）
    tables_to_clean = [
        ("users", ["fk_users_family_id", "users_ibfk_1"]),
        ("items", ["fk_items_family_id", "fk_items_creator_id", "fk_items_category_id", 
                   "items_ibfk_1", "items_ibfk_2", "items_ibfk_3"]),
        ("item_extensions", ["fk_item_extensions_item_id", "item_extensions_ibfk_1"]),
        ("chat_messages", ["fk_chat_family", "fk_chat_user", 
                           "chat_messages_ibfk_1", "chat_messages_ibfk_2"]),
        ("reminders", ["fk_reminders_family_id", "fk_reminders_item_id",
                       "reminders_ibfk_1", "reminders_ibfk_2"]),
        ("feedbacks", ["fk_feedbacks_user_id", "feedbacks_ibfk_1"]),
    ]
    
    removed_count = 0
    skipped_count = 0
    
    with engine.connect() as conn:
        for table, constraints in tables_to_clean:
            for constraint in constraints:
                try:
                    # 尝试删除外键约束
                    sql = text(f"ALTER TABLE {table} DROP FOREIGN KEY {constraint}")
                    conn.execute(sql)
                    print(f"[OK] Removed: {table}.{constraint}")
                    removed_count += 1
                except Exception as e:
                    # 约束不存在时忽略
                    error_msg = str(e)
                    if "Can't DROP" in error_msg or "doesn't exist" in error_msg:
                        # print(f"[SKIP] {table}.{constraint}")
                        skipped_count += 1
                    else:
                        print(f"[ERROR] {table}.{constraint}: {e}")
        
        conn.commit()
    
    print(f"\n[SUCCESS] Removed {removed_count} foreign key constraints")
    print(f"[INFO] Skipped {skipped_count} non-existent constraints")
    print("\n[DONE] You can now truncate tables safely!")


if __name__ == "__main__":
    print("[START] Removing foreign key constraints...")
    remove_foreign_keys()
