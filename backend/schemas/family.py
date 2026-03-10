"""
家庭相关 Schema
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FamilyCreate(BaseModel):
    """创建家庭"""
    name: str = Field(..., min_length=1, max_length=50, description="家庭名称")


class FamilyUpdate(BaseModel):
    """更新家庭"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)


class FamilyResponse(BaseModel):
    """家庭响应"""
    id: str
    name: str
    invite_code: str
    member_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class FamilyJoinRequest(BaseModel):
    """加入家庭请求"""
    invite_code: str = Field(..., min_length=6, max_length=6)