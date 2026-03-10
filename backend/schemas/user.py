"""
用户相关 Schema
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """创建用户"""
    wechat_openid: str = Field(..., description="微信OpenID")
    nickname: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    family_id: str


class UserUpdate(BaseModel):
    """更新用户"""
    nickname: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    family_id: str
    wechat_openid: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """登录请求"""
    code: str = Field(..., description="微信登录code")


class LoginResponse(BaseModel):
    """登录响应"""
    user_id: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    family_id: Optional[str] = None
    family_name: Optional[str] = None
    token: Optional[str] = None
    openid: Optional[str] = None  # 新用户时返回