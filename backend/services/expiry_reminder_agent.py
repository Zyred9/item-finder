"""
存物时自动识别：是否需加入过期/开封/保修提醒（Agent）

在创建或更新物品后调用，根据扩展信息（过期日、开封日+开封保质期、保修到期日等）
自动创建对应提醒，无需用户手动添加。
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models import Item, Reminder


def _level_for_days_left(days_left: int) -> str:
    """根据剩余天数返回提醒级别"""
    if days_left <= 0:
        return "urgent"
    if days_left <= 3:
        return "urgent"
    if days_left <= 7:
        return "warning"
    return "normal"


def _title_suffix_for_days(days_left: int, kind: str = "expire") -> str:
    """根据剩余天数返回标题后缀，与「剩余 X 天」一致，避免「即将过期」与「还有 520 天」矛盾。"""
    if kind == "expire":
        if days_left <= 0:
            return "已过期"
        if days_left <= 7:
            return "即将过期"
        if days_left <= 30:
            return "临近过期"
        return "过期提醒"
    if kind == "open":
        if days_left <= 0:
            return "开封后已过期"
        if days_left <= 7:
            return "开封后即将过期"
        if days_left <= 30:
            return "开封后临近过期"
        return "开封后保质提醒"
    if kind == "warranty":
        if days_left <= 0:
            return "保修已到期"
        if days_left <= 7:
            return "保修即将到期"
        if days_left <= 30:
            return "保修临近到期"
        return "保修到期提醒"
    return "提醒"


def _content_for_days(days_left: int, prefix: str = "还有") -> str:
    if days_left > 0:
        return f"{prefix} {days_left} 天"
    if days_left == 0:
        return "今天到期"
    return f"已过期 {-days_left} 天"


def sync_reminders_for_item(db: Session, item: Item) -> int:
    """
    根据物品扩展信息，自动判断并创建过期/开封/保修类提醒。
    若已存在同类型 pending 提醒则不重复创建；仅对「未来或今天」的日期建提醒。

    :param db: 数据库会话
    :param item: 已持久化的物品（需能访问 item.extension）
    :return: 本次新创建的提醒数量
    """
    created = 0
    today = date.today()
    ext = getattr(item, "extension", None)
    if not ext:
        return 0

    def has_pending(item_id: int, rtype: str) -> bool:
        return db.query(Reminder).filter(
            Reminder.item_id == item_id,
            Reminder.type == rtype,
            Reminder.status == "pending",
        ).first() is not None

    # 1) 过期提醒：有 expire_date，或 production_date + shelf_life_days
    remind_at = getattr(ext, "expire_date", None)
    if remind_at is None and getattr(ext, "production_date", None) and getattr(ext, "shelf_life_days", None):
        try:
            remind_at = ext.production_date + timedelta(days=int(ext.shelf_life_days))
        except (TypeError, ValueError):
            pass
    if remind_at is not None and not has_pending(item.id, "expire"):
        days_left = (remind_at - today).days
        level = _level_for_days_left(days_left)
        r = Reminder(
            family_id=item.family_id,
            item_id=item.id,
            type="expire",
            level=level,
            title=item.name,
            content=_content_for_days(days_left, "还有"),
            remind_at=remind_at,
            status="pending",
        )
        db.add(r)
        created += 1

    # 2) 保修到期提醒：warranty_date
    warranty_date = getattr(ext, "warranty_date", None)
    if warranty_date is not None and not has_pending(item.id, "warranty"):
        days_left = (warranty_date - today).days
        if days_left >= 0:  # 只创建未来的保修提醒
            level = _level_for_days_left(days_left)
            r = Reminder(
                family_id=item.family_id,
                item_id=item.id,
                type="warranty",
                level=level,
                title=f"{item.name} 保修到期",
                content=_content_for_days(days_left, "还有"),
                remind_at=warranty_date,
                status="pending",
            )
            db.add(r)
            created += 1

    if created > 0:
        db.commit()
    return created
