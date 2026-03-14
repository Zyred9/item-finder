"""
检查 item_extensions 表字段使用情况
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.base import SessionLocal
from models import ItemExtension
from sqlalchemy import inspect


def check_extension_usage():
    """检查扩展信息字段使用情况"""
    session = SessionLocal()
    
    try:
        # 获取所有扩展信息
        extensions = session.query(ItemExtension).all()
        print(f"Total extensions: {len(extensions)}\n")
        
        if not extensions:
            print("No extensions found!")
            return
        
        # 检查每个字段的使用情况
        fields = [
            'expire_date', 'production_date', 'shelf_life_days',
            'open_date', 'open_shelf_life', 'dosage',
            'document_number', 'issuer',
            'brand', 'model', 'purchase_date', 'warranty_date', 'accessories',
            'size', 'color', 'season', 'material',
            'storage_condition'
        ]
        
        print("Field usage:")
        print("-" * 60)
        
        for field in fields:
            count = sum(1 for ext in extensions if getattr(ext, field, None) is not None)
            percentage = (count / len(extensions)) * 100
            status = "[OK]" if percentage > 10 else "[LOW]" if percentage > 0 else "[NONE]"
            print(f"{status} {field:20s}: {count:3d}/{len(extensions):3d} ({percentage:5.1f}%)")
        
        print("\n" + "="*60)
        print("Recommendation:")
        print("-" * 60)
        
        # 统计使用率低的字段
        unused_fields = []
        for field in fields:
            count = sum(1 for ext in extensions if getattr(ext, field, None) is not None)
            if count == 0:
                unused_fields.append(field)
        
        if unused_fields:
            print("Fields with NO data (可以考虑删除):")
            for field in unused_fields:
                print(f"  - {field}")
        else:
            print("All fields have some data")
        
        # 统计高使用率的字段
        high_usage_fields = []
        for field in fields:
            count = sum(1 for ext in extensions if getattr(ext, field, None) is not None)
            percentage = (count / len(extensions)) * 100
            if percentage > 50:
                high_usage_fields.append((field, percentage))
        
        if high_usage_fields:
            print("\nHigh usage fields (>50%):")
            for field, pct in high_usage_fields:
                print(f"  - {field}: {pct:.1f}%")
        
    finally:
        session.close()


if __name__ == "__main__":
    check_extension_usage()
