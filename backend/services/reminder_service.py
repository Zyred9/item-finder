"""
提醒服务层
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from models import Reminder, Item, ItemExtension
from services.expiry_reminder_agent import (
    _level_for_days_left,
    _title_suffix_for_days,
    _content_for_days,
)


class ReminderService:
    """提醒业务逻辑"""
    
    @staticmethod
    def get_by_family(db: Session, family_id: int, status: Optional[str] = None,
                      level: Optional[str] = None) -> tuple[List[Reminder], dict]:
        """获取家庭提醒列表"""
        query = db.query(Reminder).filter(Reminder.family_id == family_id)
        
        if status:
            query = query.filter(Reminder.status == status)
        if level:
            query = query.filter(Reminder.level == level)
        
        query = query.order_by(Reminder.remind_at.asc())
        
        reminders = query.all()
        today = date.today()

        # 统计各级别数量
        counts = {
            "total": len(reminders),
            "urgent_count": sum(1 for r in reminders if r.level == "urgent"),
            "warning_count": sum(1 for r in reminders if r.level == "warning"),
        }
        
        # 补充物品信息及展示用 days_left / expire_at
        for reminder in reminders:
            item = db.query(Item).filter(Item.id == reminder.item_id).first()
            if item:
                reminder.item_name = item.name
                reminder.item_location = item.location
                reminder.item_photo = item.photo_path
                ext = getattr(item, "extension", None)
                expire_at = getattr(ext, "expire_date", None) if ext else None
                if expire_at is None:
                    expire_at = reminder.remind_at
                reminder.expire_at = expire_at
                reminder.days_left = (expire_at - today).days if expire_at else None

        return reminders, counts
    
    @staticmethod
    def handle(db: Session, reminder_id: int, action: str, 
               defer_days: Optional[int] = None) -> Optional[Reminder]:
        """处理提醒"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            return None
        
        if action == "done":
            reminder.status = "done"
        elif action == "ignore":
            reminder.status = "ignored"
        elif action == "defer" and defer_days:
            reminder.status = "deferred"
            reminder.deferred_to = date.today() + timedelta(days=defer_days)
        
        db.commit()
        db.refresh(reminder)
        
        return reminder
    
    @staticmethod
    def generate_expire_reminders(db: Session) -> int:
        """生成过期提醒（定时任务调用）"""
        today = date.today()
        reminder_days = [7, 3, 1, 0]  # 提醒节点
        
        count = 0
        # 查询有过期日期的物品（关联 ItemExtension 表）
        items = db.query(Item).join(
            ItemExtension, ItemExtension.item_id == Item.id
        ).filter(
            ItemExtension.expire_date.isnot(None)
        ).all()
        
        for item in items:
            extension = db.query(ItemExtension).filter(ItemExtension.item_id == item.id).first()
            if not extension or not extension.expire_date:
                continue
            
            days_left = (extension.expire_date - today).days
            
            if days_left in reminder_days:
                # 检查是否已存在提醒
                existing = db.query(Reminder).filter(
                    Reminder.item_id == item.id,
                    Reminder.type == "expire",
                    Reminder.remind_at == today
                ).first()
                
                if not existing:
                    level = "urgent" if days_left <= 1 else "warning" if days_left <= 3 else "normal"
                    reminder = Reminder(
                        family_id=item.family_id,
                        item_id=item.id,
                        type="expire",
                        level=level,
                        title=f"{item.name}即将过期",
                        content=f"还有 {days_left} 天过期" if days_left > 0 else "今天过期",
                        remind_at=today
                    )
                    db.add(reminder)
                    count += 1
        
        db.commit()
        return count

    @staticmethod
    def refresh_pending_reminders(db: Session) -> int:
        """
        每日定时任务：扫描所有待处理提醒，按当前日期重算剩余天数，
        更新 title（即将过期/临近过期/过期提醒）、level、content。
        """
        today = date.today()
        pending = db.query(Reminder).filter(Reminder.status == "pending").all()
        updated = 0
        content_prefix = {"expire": "还有", "open": "开封后还有", "warranty": "保修还有"}

        for reminder in pending:
            item = db.query(Item).filter(Item.id == reminder.item_id).first()
            if not item:
                continue
            days_left = (reminder.remind_at - today).days
            level = _level_for_days_left(days_left)
            suffix = _title_suffix_for_days(days_left, reminder.type)
            prefix = content_prefix.get(reminder.type, "还有")
            content = _content_for_days(days_left, prefix)

            reminder.level = level
            reminder.title = f"{item.name} {suffix}"
            reminder.content = content
            updated += 1

        if updated > 0:
            db.commit()
        return updated