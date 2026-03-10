"""
分类相关 Schema
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


class ExtensionFieldConfig(BaseModel):
    """扩展字段配置"""
    name: str
    label: str
    type: str  # date/text/number/textarea/select
    required: bool = False
    default: Optional[Any] = None
    options: Optional[List[str]] = None  # type=select 时使用
    reminder: bool = False  # 是否启用提醒


class CategoryResponse(BaseModel):
    """分类响应"""
    id: str
    name: str
    icon: Optional[str]
    parent_id: Optional[str]
    sort_order: int = 0
    extension_fields: Optional[List[ExtensionFieldConfig]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CategoryTreeResponse(BaseModel):
    """分类树响应（含子分类）"""
    id: str
    name: str
    icon: Optional[str]
    children: List["CategoryTreeResponse"] = []
    extension_fields: Optional[List[ExtensionFieldConfig]] = None
    
    class Config:
        from_attributes = True