"""
清理数据库：
1. 清理 categories 表中的二级分类（只保留一级分类）
2. 清理 Qdrant 中的二级分类数据
3. 删除未使用的表（locations 表）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.base import SessionLocal, engine, Base
from models import Category, Item
from sqlalchemy import text
import httpx


def cleanup_categories():
    """清理二级分类，只保留一级分类"""
    session = SessionLocal()
    
    try:
        # 查询所有有子分类的一级分类
        parent_cats = session.query(Category).filter(
            Category.parent_id.is_(None)
        ).all()
        
        print(f"Found {len(parent_cats)} parent categories")
        
        # 删除所有二级分类
        child_count = session.query(Category).filter(
            Category.parent_id.isnot(None)
        ).count()
        
        if child_count > 0:
            session.execute(text("DELETE FROM categories WHERE parent_id IS NOT NULL"))
            session.commit()
            print(f"Deleted {child_count} child categories")
        
        # 更新一级分类的 sort_order
        official_categories = [
            ("food", "食品饮料", 1),
            ("medicine", "药品健康", 2),
            ("clothing", "服饰鞋包", 3),
            ("electronics", "数码家电", 4),
            ("document", "证件文件", 5),
            ("daily", "生活用品", 6),
            ("other", "其他物品", 7),
        ]
        
        for code, name, sort_order in official_categories:
            cat = session.query(Category).filter(Category.code == code).first()
            if cat:
                cat.sort_order = sort_order
                cat.parent_id = None
                print(f"Updated: {code} - {name}")
            else:
                # 创建缺失的分类
                new_cat = Category(
                    code=code,
                    name=name,
                    icon=None,
                    parent_id=None,
                    sort_order=sort_order,
                    extension_fields=None
                )
                session.add(new_cat)
                print(f"Created: {code} - {name}")
        
        session.commit()
        
        # 验证结果
        all_cats = session.query(Category).order_by(Category.sort_order).all()
        print(f"\nFinal categories ({len(all_cats)}):")
        for cat in all_cats:
            print(f"  {cat.id}: {cat.code} - {cat.name} (sort: {cat.sort_order})")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def cleanup_qdrant():
    """清理 Qdrant 中的二级分类数据"""
    from config.settings import settings
    
    if not settings.QDRANT_URL:
        print("Qdrant not configured, skipping cleanup")
        return
    
    try:
        collection_url = f"{settings.QDRANT_URL.rstrip('/')}/collections/{settings.QDRANT_COLLECTION}"
        headers = {}
        if settings.QDRANT_API_KEY:
            headers["api-key"] = settings.QDRANT_API_KEY
        
        # 获取所有点
        print(f"Checking Qdrant collection: {settings.QDRANT_COLLECTION}")
        
        # 先检查集合是否存在
        with httpx.Client(timeout=settings.QDRANT_TIMEOUT_SECONDS) as client:
            response = client.get(collection_url, headers=headers)
            if response.status_code == 404:
                print(f"Collection {settings.QDRANT_COLLECTION} not found, skipping Qdrant cleanup")
                return
            response.raise_for_status()
        
        # 重新索引所有物品（会自动清理旧数据）
        from services.search_index_service import SearchIndexService
        from services.item_service import ItemService
        
        session = SessionLocal()
        try:
            # 获取所有物品
            items = session.query(Item).filter(Item.status == "active").all()
            print(f"Found {len(items)} active items to re-index")
            
            # 重新索引每个物品
            for i, item in enumerate(items, 1):
                try:
                    SearchIndexService.upsert_item(session, int(item.id))
                    if i % 50 == 0:
                        print(f"  Indexed {i}/{len(items)} items...")
                except Exception as e:
                    print(f"Error indexing item {item.id}: {e}")
                    continue
            
            print(f"Re-indexed {len(items)} items to Qdrant")
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"Qdrant cleanup error: {e}")


def drop_unused_tables():
    """删除未使用的表"""
    session = SessionLocal()
    
    try:
        # 检查并删除 locations 表
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = 'locations'"
        ))
        count = result.scalar()
        
        if count > 0:
            # 检查是否有外键引用
            result = session.execute(text(
                "SELECT COUNT(*) FROM information_schema.key_column_usage "
                "WHERE referenced_table_name = 'locations'"
            ))
            fk_count = result.scalar()
            
            if fk_count > 0:
                print(f"locations table has {fk_count} foreign key references, skipping deletion")
            else:
                # 先删除表中的数据
                session.execute(text("DELETE FROM locations"))
                # 删除表
                session.execute(text("DROP TABLE IF EXISTS locations"))
                session.commit()
                print("Dropped unused table: locations")
        else:
            print("locations table does not exist")
        
        # 检查其他可能的未使用表
        unused_tables = ['feedbacks']  # feedbacks 表目前也没使用
        
        for table_name in unused_tables:
            result = session.execute(text(
                f"SELECT COUNT(*) FROM information_schema.tables "
                f"WHERE table_schema = DATABASE() AND table_name = '{table_name}'"
            ))
            count = result.scalar()
            
            if count > 0:
                # 检查是否有数据
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
                
                if row_count == 0:
                    session.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    session.commit()
                    print(f"Dropped empty unused table: {table_name}")
                else:
                    print(f"Table {table_name} has {row_count} rows, keeping it")
        
    except Exception as e:
        print(f"Error dropping tables: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    print("="*60)
    print("Cleaning up database...")
    print("="*60)
    
    print("\n1. Cleaning up categories (removing child categories)...")
    cleanup_categories()
    
    print("\n2. Cleaning up Qdrant (re-indexing items)...")
    cleanup_qdrant()
    
    print("\n3. Dropping unused tables...")
    drop_unused_tables()
    
    print("\n" + "="*60)
    print("✅ Database cleanup completed!")
    print("="*60)


if __name__ == "__main__":
    main()
