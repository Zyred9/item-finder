"""
清理未使用的字段
1. Item 表：is_favorite, find_count, last_found_at
2. ItemExtension 表：size, color, season, material, storage_condition, accessories, brand, model, document_number, issuer, dosage, open_date, open_shelf_life
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.base import SessionLocal, engine
from sqlalchemy import text, inspect


def drop_item_fields():
    """删除 Item 表中的未使用字段"""
    session = SessionLocal()
    
    fields_to_drop = ['is_favorite', 'find_count', 'last_found_at']
    
    try:
        # 检查字段是否存在
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('items')]
        
        for field in fields_to_drop:
            if field in columns:
                print(f"Dropping items.{field}...")
                session.execute(text(f"ALTER TABLE items DROP COLUMN {field}"))
                print(f"  [OK] Dropped {field}")
            else:
                print(f"  [SKIP] {field} not found")
        
        session.commit()
        print("\n[OK] Item fields cleanup completed")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        session.rollback()
        raise
    finally:
        session.close()


def drop_extension_fields():
    """删除 ItemExtension 表中的未使用字段"""
    session = SessionLocal()
    
    fields_to_drop = [
        'size', 'color', 'season', 'material', 'storage_condition',
        'accessories', 'brand', 'model', 'document_number', 'issuer',
        'dosage', 'open_date', 'open_shelf_life', 'purchase_date'
    ]
    
    try:
        # 检查字段是否存在
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('item_extensions')]
        
        for field in fields_to_drop:
            if field in columns:
                print(f"Dropping item_extensions.{field}...")
                session.execute(text(f"ALTER TABLE item_extensions DROP COLUMN {field}"))
                print(f"  [OK] Dropped {field}")
            else:
                print(f"  [SKIP] {field} not found")
        
        session.commit()
        print("\n[OK] ItemExtension fields cleanup completed")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    print("="*60)
    print("Cleaning up unused database fields...")
    print("="*60)
    
    print("\n1. Cleaning Item table...")
    drop_item_fields()
    
    print("\n2. Cleaning ItemExtension table...")
    drop_extension_fields()
    
    print("\n" + "="*60)
    print("[OK] All unused fields removed!")
    print("="*60)


if __name__ == "__main__":
    main()
