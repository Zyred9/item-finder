"""
清理孤儿提醒（物品已删除的提醒）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.base import SessionLocal
from models import Reminder, Item
from sqlalchemy import text


def cleanup_orphan_reminders():
    """清理物品已删除的提醒"""
    session = SessionLocal()
    
    try:
        # 方法 1：使用 SQL 直接删除（绕过外键检查）
        result = session.execute(text("""
            DELETE r FROM reminders r
            LEFT JOIN items i ON r.item_id = i.id
            WHERE i.id IS NULL
        """))
        deleted_count = result.rowcount
        session.commit()
        
        print(f"[OK] Deleted {deleted_count} orphan reminders (SQL method)")
        
        # 验证
        remaining = session.query(Reminder).filter(
            Reminder.type == 'expire'
        ).count()
        
        print(f"Remaining expire reminders: {remaining}")
        
        return deleted_count
        
    except Exception as e:
        print(f"[ERROR] {e}")
        session.rollback()
        return 0
    finally:
        session.close()


def sync_reminders_for_current_items():
    """为当前所有物品重新生成提醒"""
    from services.expiry_reminder_agent import sync_reminders_for_item
    
    session = SessionLocal()
    
    try:
        items = session.query(Item).filter(Item.status == 'active').all()
        print(f"\nFound {len(items)} active items")
        
        created_count = 0
        for item in items:
            try:
                count = sync_reminders_for_item(session, item)
                if count > 0:
                    created_count += count
                    print(f"  Created {count} reminders for: {item.name}")
            except Exception as e:
                print(f"  Error syncing {item.name}: {e}")
                continue
        
        session.commit()
        
        print(f"\n[OK] Created {created_count} new reminders")
        return created_count
        
    except Exception as e:
        print(f"[ERROR] {e}")
        session.rollback()
        return 0
    finally:
        session.close()


def main():
    print("="*60)
    print("Cleaning up orphan reminders...")
    print("="*60)
    
    cleanup_orphan_reminders()
    
    print("\nSyncing reminders for current items...")
    sync_reminders_for_current_items()
    
    print("\n" + "="*60)
    print("[OK] Done!")
    print("="*60)


if __name__ == "__main__":
    main()
