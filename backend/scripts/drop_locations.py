import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.base import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # 删除 locations 表
    db.execute(text("DROP TABLE IF EXISTS locations"))
    db.commit()
    print("[OK] Dropped locations table")
    
    # 验证
    result = db.execute(text("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() AND table_name = 'locations'
    """))
    count = result.scalar()
    
    if count == 0:
        print("[OK] locations table successfully deleted")
    else:
        print("[ERROR] locations table still exists")
    
finally:
    db.close()
