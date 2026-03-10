"""
物品相关 Schema
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List


class ItemExtensionCreate(BaseModel):
    """物品扩展信息创建"""
    # 药品
    expire_date: Optional[date] = None
    production_date: Optional[date] = None
    shelf_life_days: Optional[int] = None
    open_date: Optional[date] = None
    open_shelf_life: Optional[int] = None
    dosage: Optional[str] = None
    # 证件
    document_number: Optional[str] = None
    issuer: Optional[str] = None
    # 电器
    brand: Optional[str] = None
    model: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_date: Optional[date] = None
    accessories: Optional[str] = None
    # 衣物
    size: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    material: Optional[str] = None
    # 食品
    storage_condition: Optional[str] = None


class ItemExtensionResponse(BaseModel):
    """物品扩展信息响应"""
    expire_date: Optional[date] = None
    production_date: Optional[date] = None
    shelf_life_days: Optional[int] = None
    open_date: Optional[date] = None
    open_shelf_life: Optional[int] = None
    dosage: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_date: Optional[date] = None
    size: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    
    class Config:
        from_attributes = True


class ItemCreate(BaseModel):
    """创建物品"""
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    photo_path: Optional[str] = None
    category_id: Optional[str] = None
    extension: Optional[ItemExtensionCreate] = None


class ItemUpdate(BaseModel):
    """更新物品"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    photo_path: Optional[str] = None
    category_id: Optional[str] = None
    extension: Optional[ItemExtensionCreate] = None


class ItemResponse(BaseModel):
    """物品响应"""
    id: str
    family_id: str
    creator_id: str
    creator_name: Optional[str] = None
    name: str
    location: str
    description: Optional[str]
    photo_path: Optional[str]
    category_id: Optional[str]
    category_name: Optional[str] = None
    status: str = "active"
    is_favorite: bool = False
    find_count: int = 0
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
    q: str = Field(..., min_length=1)
    family_id: str
    limit: int = Field(20, ge=1, le=100)