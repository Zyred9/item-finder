"""
反馈相关 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    """提交反馈请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="反馈内容")
    contact: Optional[str] = Field(None, max_length=100, description="联系方式（选填）")


class FeedbackResponse(BaseModel):
    """反馈提交响应"""
    id: int
    content: str
    contact: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
