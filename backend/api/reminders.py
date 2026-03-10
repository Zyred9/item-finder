"""
提醒相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db
from schemas import Response
from schemas.reminder import ReminderResponse, ReminderListResponse, ReminderHandleRequest
from services import ReminderService

router = APIRouter(prefix="/reminders", tags=["智能提醒"])


def get_current_user(user_id: Optional[str] = Header(None, alias="X-User-Id")) -> str:
    """获取当前用户ID"""
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")
    return user_id


@router.get("", response_model=Response[ReminderListResponse])
async def get_reminders(
    family_id: str,
    status: Optional[str] = None,
    level: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取提醒列表"""
    reminders, counts = ReminderService.get_by_family(
        db, family_id, status=status, level=level
    )
    
    result = []
    for r in reminders:
        result.append(ReminderResponse(
            id=r.id,
            family_id=r.family_id,
            item_id=r.item_id,
            type=r.type,
            level=r.level,
            title=r.title,
            content=r.content,
            remind_at=r.remind_at,
            status=r.status,
            deferred_to=r.deferred_to,
            created_at=r.created_at,
            days_left=getattr(r, "days_left", None),
            expire_at=getattr(r, "expire_at", None),
            item_name=getattr(r, "item_name", None),
            item_location=getattr(r, "item_location", None),
            item_photo=getattr(r, "item_photo", None),
        ))
    
    return Response(data=ReminderListResponse(
        total=counts["total"],
        urgent_count=counts["urgent_count"],
        warning_count=counts["warning_count"],
        reminders=result
    ))


@router.put("/{reminder_id}", response_model=Response[ReminderResponse])
async def handle_reminder(
    reminder_id: str,
    request: ReminderHandleRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """处理提醒"""
    reminder = ReminderService.handle(
        db, reminder_id, request.action, request.defer_days
    )
    
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")
    
    return Response(data=ReminderResponse(
        id=reminder.id,
        family_id=reminder.family_id,
        item_id=reminder.item_id,
        type=reminder.type,
        level=reminder.level,
        title=reminder.title,
        content=reminder.content,
        remind_at=reminder.remind_at,
        status=reminder.status,
        deferred_to=reminder.deferred_to,
        created_at=reminder.created_at
    ))