"""
分类相关 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from models import get_db, Category
from schemas import Response
from schemas.category import CategoryResponse, CategoryTreeResponse, ExtensionFieldConfig

router = APIRouter(prefix="/categories", tags=["分类管理"])


# 默认分类数据（可后续移到数据库）
DEFAULT_CATEGORIES = [
    {
        "id": "medicine",
        "name": "药品健康",
        "icon": "💊",
        "children": [
            {"id": "prescription", "name": "处方药"},
            {"id": "otc", "name": "非处方药"},
            {"id": "supplement", "name": "保健品"},
            {"id": "device", "name": "医疗器械"}
        ],
        "extension_fields": [
            {"name": "expire_date", "label": "有效期", "type": "date", "required": False, "reminder": True},
            {"name": "open_date", "label": "开封日期", "type": "date", "required": False},
            {"name": "open_shelf_life", "label": "开封后保质期(天)", "type": "number", "required": False},
            {"name": "dosage", "label": "用法用量", "type": "text", "required": False}
        ]
    },
    {
        "id": "food",
        "name": "食品饮料",
        "icon": "🍔",
        "children": [
            {"id": "snacks", "name": "零食"},
            {"id": "condiment", "name": "调味品"},
            {"id": "baby_food", "name": "婴幼儿食品"}
        ],
        "extension_fields": [
            {"name": "expire_date", "label": "有效期", "type": "date", "required": False, "reminder": True},
            {"name": "production_date", "label": "生产日期", "type": "date", "required": False},
            {"name": "storage_condition", "label": "储存条件", "type": "select", "required": False, 
             "options": ["常温", "冷藏", "冷冻"]}
        ]
    },
    {
        "id": "document",
        "name": "证件文件",
        "icon": "📄",
        "children": [
            {"id": "id_card", "name": "身份证"},
            {"id": "passport", "name": "护照"},
            {"id": "bank_card", "name": "银行卡"},
            {"id": "contract", "name": "合同"},
            {"id": "receipt", "name": "票据"}
        ],
        "extension_fields": [
            {"name": "expire_date", "label": "有效期", "type": "date", "required": False, "reminder": True},
            {"name": "document_number", "label": "证件号码", "type": "text", "required": False},
            {"name": "issuer", "label": "发证机关", "type": "text", "required": False}
        ]
    },
    {
        "id": "electronics",
        "name": "电器数码",
        "icon": "🔌",
        "children": [
            {"id": "kitchen_appliance", "name": "厨房电器"},
            {"id": "home_appliance", "name": "生活电器"},
            {"id": "digital", "name": "数码产品"},
            {"id": "accessory", "name": "配件"}
        ],
        "extension_fields": [
            {"name": "brand", "label": "品牌", "type": "text", "required": False},
            {"name": "model", "label": "型号", "type": "text", "required": False},
            {"name": "purchase_date", "label": "购买日期", "type": "date", "required": False},
            {"name": "warranty_date", "label": "保修到期", "type": "date", "required": False, "reminder": True}
        ]
    },
    {
        "id": "clothing",
        "name": "服饰鞋包",
        "icon": "👕",
        "children": [
            {"id": "tops", "name": "上衣"},
            {"id": "pants", "name": "裤子"},
            {"id": "shoes", "name": "鞋子"},
            {"id": "bags", "name": "包包"}
        ],
        "extension_fields": [
            {"name": "size", "label": "尺码", "type": "text", "required": False},
            {"name": "color", "label": "颜色", "type": "text", "required": False},
            {"name": "season", "label": "季节", "type": "select", "required": False, 
             "options": ["春", "夏", "秋", "冬"]}
        ]
    },
    {
        "id": "other",
        "name": "其他",
        "icon": "📦",
        "children": []
    }
]


@router.get("", response_model=Response[List[CategoryTreeResponse]])
async def get_categories(db: Session = Depends(get_db)):
    """获取分类列表（树形结构）"""
    # TODO: 从数据库读取，目前返回默认数据
    result = []
    for cat in DEFAULT_CATEGORIES:
        result.append(CategoryTreeResponse(
            id=cat["id"],
            name=cat["name"],
            icon=cat.get("icon"),
            children=[
                CategoryTreeResponse(id=c["id"], name=c["name"], icon=None, children=[])
                for c in cat.get("children", [])
            ],
            extension_fields=[
                ExtensionFieldConfig(**f) for f in cat.get("extension_fields", [])
            ] if cat.get("extension_fields") else None
        ))
    
    return Response(data=result)


@router.get("/{category_id}", response_model=Response[CategoryResponse])
async def get_category(category_id: str, db: Session = Depends(get_db)):
    """获取分类详情"""
    for cat in DEFAULT_CATEGORIES:
        if cat["id"] == category_id:
            return Response(data=CategoryResponse(
                id=cat["id"],
                name=cat["name"],
                icon=cat.get("icon"),
                extension_fields=[
                    ExtensionFieldConfig(**f) for f in cat.get("extension_fields", [])
                ] if cat.get("extension_fields") else None
            ))
    
        for child in cat.get("children", []):
            if child["id"] == category_id:
                return Response(data=CategoryResponse(
                    id=child["id"],
                    name=child["name"],
                    parent_id=cat["id"]
                ))
    
    return Response(code=404, message="分类不存在")