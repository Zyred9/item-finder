"""
提醒相关 Schema
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List


class ReminderResponse(BaseModel):
    """提醒响应"""
    id: int
    family_id: int
    item_id: int
    type: str
    level: str
    title: str
    content: Optional[str]
    remind_at: date
    status: str
    deferred_to: Optional[date]
    created_at: datetime

    # 展示用：剩余天数、过期日（首页/列表时间标签与内容拼接）
    days_left: Optional[int] = None
    expire_at: Optional[date] = None

    # 关联物品信息
    item_name: Optional[str] = None
    item_location: Optional[str] = None
    item_photo: Optional[str] = None

    class Config:
        from_attributes = True


class ReminderListResponse(BaseModel):
    """提醒列表响应"""
    total: int
    urgent_count: int = 0
    warning_count: int = 0
    reminders: List[ReminderResponse]


class ReminderHandleRequest(BaseModel):
    """处理提醒请求"""
    action: str = Field(..., pattern="^(done|ignore|defer)$")
    defer_days: Optional[int] = Field(None, ge=1, le=30, description="延期天数")