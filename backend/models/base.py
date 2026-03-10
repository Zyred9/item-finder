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
    """初始化默认分类数据"""
    from models import Category
    
    db = SessionLocal()
    try:
        # 检查是否已有分类
        if db.query(Category).count() > 0:
            print("[INFO] Categories already exist, skipping initialization")
            return
        
        # 默认分类数据
        default_categories = [
            # 主分类
            {"id": "medicine", "name": "药品健康", "icon": "💊", "parent_id": None},
            {"id": "food", "name": "食品饮料", "icon": "🍔", "parent_id": None},
            {"id": "document", "name": "证件文件", "icon": "📄", "parent_id": None},
            {"id": "electronics", "name": "电器数码", "icon": "🔌", "parent_id": None},
            {"id": "clothing", "name": "服饰鞋包", "icon": "👕", "parent_id": None},
            {"id": "other", "name": "其他", "icon": "📦", "parent_id": None},
            # 药品子分类
            {"id": "prescription", "name": "处方药", "icon": None, "parent_id": "medicine"},
            {"id": "otc", "name": "非处方药", "icon": None, "parent_id": "medicine"},
            {"id": "supplement", "name": "保健品", "icon": None, "parent_id": "medicine"},
            {"id": "device", "name": "医疗器械", "icon": None, "parent_id": "medicine"},
            # 食品子分类
            {"id": "snacks", "name": "零食", "icon": None, "parent_id": "food"},
            {"id": "condiment", "name": "调味品", "icon": None, "parent_id": "food"},
            {"id": "baby_food", "name": "婴幼儿食品", "icon": None, "parent_id": "food"},
            # 证件子分类
            {"id": "id_card", "name": "身份证", "icon": None, "parent_id": "document"},
            {"id": "passport", "name": "护照", "icon": None, "parent_id": "document"},
            {"id": "bank_card", "name": "银行卡", "icon": None, "parent_id": "document"},
            {"id": "contract", "name": "合同", "icon": None, "parent_id": "document"},
            {"id": "receipt", "name": "票据", "icon": None, "parent_id": "document"},
            # 电器子分类
            {"id": "kitchen_appliance", "name": "厨房电器", "icon": None, "parent_id": "electronics"},
            {"id": "home_appliance", "name": "生活电器", "icon": None, "parent_id": "electronics"},
            {"id": "digital", "name": "数码产品", "icon": None, "parent_id": "electronics"},
            {"id": "accessory", "name": "配件", "icon": None, "parent_id": "electronics"},
            # 服饰子分类
            {"id": "tops", "name": "上衣", "icon": None, "parent_id": "clothing"},
            {"id": "pants", "name": "裤子", "icon": None, "parent_id": "clothing"},
            {"id": "shoes", "name": "鞋子", "icon": None, "parent_id": "clothing"},
            {"id": "bags", "name": "包包", "icon": None, "parent_id": "clothing"},
        ]
        
        for cat_data in default_categories:
            category = Category(
                id=cat_data["id"],
                name=cat_data["name"],
                icon=cat_data.get("icon"),
                parent_id=cat_data.get("parent_id")
            )
            db.add(category)
        
        db.commit()
        print(f"[OK] Initialized {len(default_categories)} default categories")
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize categories: {e}")
        db.rollback()
    finally:
        db.close()