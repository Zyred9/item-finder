"""
分类相关 API（从数据库读取，id 为整型自增）
只保留一级分类，共 7 个
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from models import get_db, Category
from schemas import Response
from schemas.category import CategoryResponse, CategoryTreeResponse, ExtensionFieldConfig

router = APIRouter(prefix="/categories", tags=["分类管理"])


def _parse_extension_fields(raw: Optional[str]) -> Optional[List[ExtensionFieldConfig]]:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return [ExtensionFieldConfig(**x) for x in data] if isinstance(data, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("", response_model=Response[List[CategoryResponse]])
async def get_categories(db: Session = Depends(get_db)):
    """获取分类列表（只返回一级分类，按 sort_order 排序）"""
    cats = db.query(Category).order_by(Category.sort_order, Category.id).all()
    
    result = []
    for cat in cats:
        result.append(CategoryResponse(
            id=int(cat.id),
            name=cat.name,
            icon=cat.icon,
            parent_id=None,  # 一级分类无父级
            sort_order=cat.sort_order or 0,
            extension_fields=_parse_extension_fields(cat.extension_fields),
            created_at=cat.created_at,
        ))
    
    return Response(data=result)


@router.get("/{category_id}", response_model=Response[CategoryResponse])
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """获取分类详情"""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    return Response(data=CategoryResponse(
        id=int(cat.id),
        name=cat.name,
        icon=cat.icon,
        parent_id=None,  # 一级分类无父级
        sort_order=cat.sort_order or 0,
        extension_fields=_parse_extension_fields(cat.extension_fields),
        created_at=cat.created_at,
    ))
