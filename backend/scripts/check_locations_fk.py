import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.base import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # 检查外键引用
    result = db.execute(text("""
        SELECT table_name, column_name 
        FROM information_schema.key_column_usage 
        WHERE referenced_table_name = 'locations'
    """))
    rows = result.fetchall()
    
    if rows:
        print("locations table is referenced by:")
        for row in rows:
            print(f"  Table: {row[0]}, Column: {row[1]}")
    else:
        print("No foreign key references to locations table")
    
    # 检查 locations 表的数据
    result = db.execute(text("SELECT COUNT(*) FROM locations"))
    count = result.scalar()
    print(f"\nlocations table has {count} rows")
    
finally:
    db.close()
