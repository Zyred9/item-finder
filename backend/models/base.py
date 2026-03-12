"""
数据库基础配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config.settings import settings

# 创建引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # MySQL 连接池健康检查
    pool_recycle=3600    # 连接回收时间
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表 + 初始化默认数据）"""
    # 导入所有模型，确保它们被注册
    from models import User, Family, Item, ItemExtension, Category, Location, Reminder, ChatMessage
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")
    
    # 初始化默认分类
    _init_categories()


def _init_categories():
    """初始化默认分类数据（id 自增，业务编码用 code）"""
    from models import Category

    db = SessionLocal()
    try:
        if db.query(Category).count() > 0:
            print("[INFO] Categories already exist, skipping initialization")
            return

        default_categories = [
            {"code": "medicine", "name": "药品健康", "icon": "💊", "parent_code": None},
            {"code": "food", "name": "食品饮料", "icon": "🍔", "parent_code": None},
            {"code": "document", "name": "证件文件", "icon": "📄", "parent_code": None},
            {"code": "electronics", "name": "电器数码", "icon": "🔌", "parent_code": None},
            {"code": "clothing", "name": "服饰鞋包", "icon": "👕", "parent_code": None},
            {"code": "other", "name": "其他", "icon": "📦", "parent_code": None},
            {"code": "prescription", "name": "处方药", "icon": None, "parent_code": "medicine"},
            {"code": "otc", "name": "非处方药", "icon": None, "parent_code": "medicine"},
            {"code": "supplement", "name": "保健品", "icon": None, "parent_code": "medicine"},
            {"code": "device", "name": "医疗器械", "icon": None, "parent_code": "medicine"},
            {"code": "snacks", "name": "零食", "icon": None, "parent_code": "food"},
            {"code": "condiment", "name": "调味品", "icon": None, "parent_code": "food"},
            {"code": "baby_food", "name": "婴幼儿食品", "icon": None, "parent_code": "food"},
            {"code": "id_card", "name": "身份证", "icon": None, "parent_code": "document"},
            {"code": "passport", "name": "护照", "icon": None, "parent_code": "document"},
            {"code": "bank_card", "name": "银行卡", "icon": None, "parent_code": "document"},
            {"code": "contract", "name": "合同", "icon": None, "parent_code": "document"},
            {"code": "receipt", "name": "票据", "icon": None, "parent_code": "document"},
            {"code": "kitchen_appliance", "name": "厨房电器", "icon": None, "parent_code": "electronics"},
            {"code": "home_appliance", "name": "生活电器", "icon": None, "parent_code": "electronics"},
            {"code": "digital", "name": "数码产品", "icon": None, "parent_code": "electronics"},
            {"code": "accessory", "name": "配件", "icon": None, "parent_code": "electronics"},
            {"code": "tops", "name": "上衣", "icon": None, "parent_code": "clothing"},
            {"code": "pants", "name": "裤子", "icon": None, "parent_code": "clothing"},
            {"code": "shoes", "name": "鞋子", "icon": None, "parent_code": "clothing"},
            {"code": "bags", "name": "包包", "icon": None, "parent_code": "clothing"},
        ]
        code_to_id = {}
        for row in default_categories:
            parent_id = code_to_id.get(row["parent_code"]) if row.get("parent_code") else None
            cat = Category(
                code=row["code"],
                name=row["name"],
                icon=row.get("icon"),
                parent_id=parent_id,
            )
            db.add(cat)
            db.flush()
            code_to_id[row["code"]] = cat.id
        db.commit()
        print(f"[OK] Initialized {len(default_categories)} default categories")
    except Exception as e:
        print(f"[ERROR] Failed to initialize categories: {e}")
        db.rollback()
    finally:
        db.close()