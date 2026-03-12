"""
分类相关 API（从数据库读取，id 为整型自增）
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


def _build_tree(db: Session) -> List[CategoryTreeResponse]:
    """从数据库构建分类树"""
    all_cats = db.query(Category).order_by(Category.sort_order, Category.id).all()
    by_parent = {}
    for c in all_cats:
        pid = c.parent_id
        if pid not in by_parent:
            by_parent[pid] = []
        by_parent[pid].append(c)

    def children_of(parent_id: Optional[int]) -> List[CategoryTreeResponse]:
        nodes = by_parent.get(parent_id) or []
        return [
            CategoryTreeResponse(
                id=int(n.id),
                name=n.name,
                icon=n.icon,
                children=children_of(n.id),
                extension_fields=_parse_extension_fields(n.extension_fields),
            )
            for n in nodes
        ]

    return children_of(None)


@router.get("", response_model=Response[List[CategoryTreeResponse]])
async def get_categories(db: Session = Depends(get_db)):
    """获取分类列表（树形结构，从数据库读取）"""
    result = _build_tree(db)
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
        parent_id=int(cat.parent_id) if cat.parent_id else None,
        sort_order=cat.sort_order or 0,
        extension_fields=_parse_extension_fields(cat.extension_fields),
        created_at=cat.created_at,
    ))
