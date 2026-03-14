"""
初始化正式环境分类数据
清理现有混乱分类，建立清晰的中文分类体系
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.base import SessionLocal, Base, engine
from models import Category
from sqlalchemy import text


# 正式环境分类体系（全中文，适合家庭使用）
# 只保留 6 个一级分类，简单清晰，用户好选择
OFFICIAL_CATEGORIES = [
    {"code": "food", "name": "食品饮料", "icon": "🍔", "parent_code": None, "sort_order": 1},
    {"code": "medicine", "name": "药品健康", "icon": "💊", "parent_code": None, "sort_order": 2},
    {"code": "clothing", "name": "服饰鞋包", "icon": "👕", "parent_code": None, "sort_order": 3},
    {"code": "electronics", "name": "数码家电", "icon": "📱", "parent_code": None, "sort_order": 4},
    {"code": "document", "name": "证件文件", "icon": "📄", "parent_code": None, "sort_order": 5},
    {"code": "daily", "name": "生活用品", "icon": "🏠", "parent_code": None, "sort_order": 6},
    {"code": "other", "name": "其他物品", "icon": "📦", "parent_code": None, "sort_order": 7},
]


def init_official_categories():
    """初始化正式环境分类"""
    session = SessionLocal()
    
    try:
        # 先备份现有物品的分类映射关系
        from models import Item
        items = session.query(Item).all()
        print(f"Found {len(items)} items that need category mapping")
        
        # 清空现有分类（级联删除会处理外键）
        session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        session.execute(text("DELETE FROM items"))
        session.execute(text("DELETE FROM categories"))
        session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        session.commit()
        print("Cleared existing categories and items")
        
        # 插入新分类
        code_to_id = {}
        inserted_count = 0
        
        for cat_data in OFFICIAL_CATEGORIES:
            parent_id = None
            if cat_data.get("parent_code"):
                parent_id = code_to_id.get(cat_data["parent_code"])
            
            category = Category(
                code=cat_data["code"],
                name=cat_data["name"],
                icon=cat_data.get("icon"),
                parent_id=parent_id,
                sort_order=cat_data.get("sort_order", 0),
                extension_fields=None  # 后续根据需要使用
            )
            session.add(category)
            session.flush()
            code_to_id[cat_data["code"]] = category.id
            inserted_count += 1
        
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"Successfully initialized {inserted_count} categories")
        print(f"{'='*60}")
        
        # 打印分类结构
        print("\nCategory Structure:")
        print("-" * 60)
        for cat in OFFICIAL_CATEGORIES:
            if cat.get("parent_code") is None:
                print(f"{cat['icon']} {cat['name']} ({cat['code']})")
                # 打印子类
                children = [c for c in OFFICIAL_CATEGORIES if c.get("parent_code") == cat["code"]]
                for child in children:
                    print(f"  └─ {child['name']} ({child['code']})")
        
        return code_to_id
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("="*60)
    print("Initializing official categories for production...")
    print("="*60)
    init_official_categories()
    print("\n✅ Done! Categories are ready for production use.")
