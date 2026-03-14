"""
为所有已有物品重新生成过期提醒
用于初始化或修复提醒数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.base import SessionLocal
from models import Item, ItemExtension
from services.expiry_reminder_agent import sync_reminders_for_item


def sync_all_reminders(family_id=2):
    """为指定家庭的所有物品生成提醒"""
    session = SessionLocal()
    
    try:
        # 获取所有有过期信息的物品
        items = session.query(Item).join(ItemExtension).filter(
            Item.family_id == family_id,
            Item.status == "active",
            ItemExtension.expire_date.isnot(None)
        ).all()
        
        print(f"Found {len(items)} items with expiry info")
        
        created_count = 0
        for item in items:
            try:
                created = sync_reminders_for_item(session, item)
                if created > 0:
                    created_count += created
                    print(f"Created {created} reminders for: {item.name} @ {item.location}")
            except Exception as e:
                print(f"Error syncing {item.name}: {e}")
                continue
        
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"Successfully created {created_count} new reminders")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    print("="*60)
    print("Syncing expiry reminders for all items...")
    print("="*60)
    sync_all_reminders()
    print("\nDone!")


if __name__ == "__main__":
    main()
