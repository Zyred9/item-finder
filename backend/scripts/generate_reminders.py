"""
为已过期和临期物品生成提醒数据
"""

import sys
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_db, Item, ItemExtension, Reminder
from sqlalchemy.orm import Session

def generate_reminders(db: Session):
    """为过期/临期物品生成提醒"""

    today = datetime.now().date()
    print(f"开始生成提醒数据... (今天：{today})")

    # 查询所有有 expire_date 的物品
    items_with_ext = db.query(Item, ItemExtension).join(
        ItemExtension, ItemExtension.item_id == Item.id
    ).filter(
        ItemExtension.expire_date.isnot(None),
        Item.status == 'active'
    ).all()

    print(f"找到 {len(items_with_ext)} 个有过期日期的物品")

    reminders_to_add = []
    stats = {'expired': 0, 'expiring_7days': 0, 'expiring_30days': 0, 'normal': 0}

    for item, ext in items_with_ext:
        days_left = (ext.expire_date - today).days

        # 只为已过期或 60 天内过期的物品生成提醒
        if days_left <= 60:
            # 检查是否已存在提醒
            existing = db.query(Reminder).filter(
                Reminder.item_id == item.id,
                Reminder.type == 'expire',
                Reminder.status == 'pending'
            ).first()

            if existing:
                print(f"  跳过：{item.name} - 提醒已存在")
                continue

            # 确定级别和标题
            if days_left < 0:
                level = 'urgent'
                title = f"{item.name} 已过期"
                content = f"已过期 {abs(days_left)} 天"
                stats['expired'] += 1
            elif days_left <= 1:
                level = 'urgent'
                title = f"{item.name} 今天过期"
                content = "今天过期"
                stats['expiring_7days'] += 1
            elif days_left <= 3:
                level = 'urgent'
                title = f"{item.name} 即将过期"
                content = f"还有 {days_left} 天过期"
                stats['expiring_7days'] += 1
            elif days_left <= 7:
                level = 'warning'
                title = f"{item.name} 即将过期"
                content = f"还有 {days_left} 天过期"
                stats['expiring_7days'] += 1
            elif days_left <= 30:
                level = 'warning'
                title = f"{item.name} 临近过期"
                content = f"还有 {days_left} 天过期"
                stats['expiring_30days'] += 1
            else:  # 31-60 天
                level = 'normal'
                title = f"{item.name} 注意保质期"
                content = f"还有 {days_left} 天过期"
                stats['expiring_30days'] += 1

            # 创建提醒
            remind_at = today
            if days_left < 0:
                # 已过期的物品，remind_at 设为过期那天
                remind_at = ext.expire_date

            reminder = Reminder(
                family_id=item.family_id,
                item_id=item.id,
                type='expire',
                level=level,
                title=title,
                content=content,
                remind_at=remind_at,
                status='pending'
            )
            reminders_to_add.append(reminder)
            print(f"  添加：{item.name} - {days_left}天 - {level}")
        else:
            stats['normal'] += 1

    # 批量插入
    if reminders_to_add:
        for r in reminders_to_add:
            db.add(r)
        db.commit()
        print(f"\n成功生成 {len(reminders_to_add)} 条提醒")
    else:
        print("\n没有需要生成的提醒")

    print("\n统计:")
    print(f"  已过期：{stats['expired']}")
    print(f"  7 天内过期：{stats['expiring_7days']}")
    print(f"  30 天内过期：{stats['expiring_30days']}")
    print(f"  正常 (>60 天): {stats['normal']}")

    return len(reminders_to_add)

def main():
    db = next(get_db())
    try:
        count = generate_reminders(db)
        print(f"\n完成！共生成了 {count} 条提醒")
    except Exception as e:
        db.rollback()
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()
