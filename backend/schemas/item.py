"""
物品相关 Schema
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List


class ItemExtensionCreate(BaseModel):
    """物品扩展信息创建（只保留核心字段）"""
    expire_date: Optional[date] = None
    production_date: Optional[date] = None
    shelf_life_days: Optional[int] = None
    warranty_date: Optional[date] = None


class ItemExtensionResponse(BaseModel):
    """物品扩展信息响应（只保留核心字段）"""
    expire_date: Optional[date] = None
    production_date: Optional[date] = None
    shelf_life_days: Optional[int] = None
    warranty_date: Optional[date] = None
    
    class Config:
        from_attributes = True


class ItemCreate(BaseModel):
    """创建物品"""
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    photo_path: Optional[str] = None
    category_id: Optional[int] = None
    extension: Optional[ItemExtensionCreate] = None


class ItemUpdate(BaseModel):
    """更新物品"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    photo_path: Optional[str] = None
    category_id: Optional[int] = None
    extension: Optional[ItemExtensionCreate] = None


class ItemResponse(BaseModel):
    """物品响应"""
    id: int
    family_id: int
    creator_id: int
    creator_name: Optional[str] = None
    name: str
    location: str
    description: Optional[str]
    photo_path: Optional[str]
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    extension: Optional[ItemExtensionResponse] = None
    
    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """物品列表响应"""
    total: int
    items: List[ItemResponse]


class ItemSearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=20, ge=1, le=100)
