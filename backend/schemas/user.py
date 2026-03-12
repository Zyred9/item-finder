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
    family_id: Optional[int] = None


class UserUpdate(BaseModel):
    """更新用户（头像仅支持从微信登录时拉取，此处不可修改）"""
    nickname: Optional[str] = Field(None, max_length=50)
    remark: Optional[str] = Field(None, max_length=100, description="家庭内备注名")


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    family_id: Optional[int] = None
    wechat_openid: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    is_admin: bool
    remark: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """登录请求"""
    code: str = Field(..., description="微信登录code")
    nickname: Optional[str] = Field(None, max_length=50, description="微信昵称（从微信拉取，仅登录时写入）")
    avatar_url: Optional[str] = Field(None, max_length=500, description="微信头像URL（从微信拉取，仅登录时写入，不支持修改）")


class LoginResponse(BaseModel):
    """登录响应"""
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    family_id: Optional[int] = None
    family_name: Optional[str] = None
    token: Optional[str] = None
    openid: Optional[str] = None  # 新用户时返回