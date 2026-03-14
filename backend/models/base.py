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


# ===== 各分类扩展字段配置（code -> fields） =====
# 每次修改这里的内容，启动时会自动同步到数据库（已有分类也会更新）
_CATEGORY_EXTENSION_FIELDS = {
    # ---- 食品饮料类 ----
    "food": [
        {"name": "production_date", "label": "生产日期", "type": "date", "required": False, "reminder": False},
        {"name": "expire_date",     "label": "过期日期", "type": "date", "required": False, "reminder": True},
        {"name": "open_date",       "label": "开封日期", "type": "date", "required": False, "reminder": False},
        {"name": "open_shelf_life", "label": "开封后保质(天)", "type": "number", "required": False, "reminder": False},
    ],
    "snacks":    "food",
    "condiment": "food",
    "baby_food": "food",
    # ---- 药品健康类 ----
    "medicine": [
        {"name": "production_date", "label": "生产日期", "type": "date",   "required": False, "reminder": False},
        {"name": "expire_date",     "label": "过期日期", "type": "date",   "required": False, "reminder": True},
        {"name": "open_date",       "label": "开封日期", "type": "date",   "required": False, "reminder": False},
        {"name": "open_shelf_life", "label": "开封后保质(天)", "type": "number", "required": False, "reminder": False},
        {"name": "dosage",          "label": "用量/次",  "type": "text",   "required": False, "reminder": False},
    ],
    "prescription": "medicine",
    "otc":          "medicine",
    "supplement":   "medicine",
    "device": [
        {"name": "purchase_date",  "label": "购买日期",  "type": "date", "required": False, "reminder": False},
        {"name": "warranty_date",  "label": "保修到期",  "type": "date", "required": False, "reminder": True},
    ],
    # ---- 证件文件类 ----
    "document": [
        {"name": "issue_date",  "label": "签发日期", "type": "date", "required": False, "reminder": False},
        {"name": "expire_date", "label": "到期日",   "type": "date", "required": False, "reminder": True},
    ],
    "id_card":  "document",
    "passport": "document",
    "bank_card": [
        {"name": "expire_date", "label": "有效期至", "type": "date", "required": False, "reminder": True},
    ],
    "contract": [
        {"name": "sign_date",   "label": "签署日期", "type": "date", "required": False, "reminder": False},
        {"name": "expire_date", "label": "到期日",   "type": "date", "required": False, "reminder": True},
        {"name": "party",       "label": "对方单位", "type": "text", "required": False, "reminder": False},
    ],
    "receipt": [
        {"name": "issue_date", "label": "开票日期", "type": "date", "required": False, "reminder": False},
        {"name": "amount",     "label": "金额",     "type": "text", "required": False, "reminder": False},
    ],
    # ---- 电器数码类 ----
    "electronics": [
        {"name": "brand",         "label": "品牌",     "type": "text", "required": False, "reminder": False},
        {"name": "model_no",      "label": "型号",     "type": "text", "required": False, "reminder": False},
        {"name": "purchase_date", "label": "购买日期", "type": "date", "required": False, "reminder": False},
        {"name": "warranty_date", "label": "保修到期", "type": "date", "required": False, "reminder": True},
    ],
    "kitchen_appliance": "electronics",
    "home_appliance":    "electronics",
    "digital":           "electronics",
    "accessory":         "electronics",
    # ---- 服饰鞋包类 ----
    "clothing": [
        {"name": "brand",         "label": "品牌",     "type": "text", "required": False, "reminder": False},
        {"name": "size",          "label": "尺码",     "type": "text", "required": False, "reminder": False},
        {"name": "purchase_date", "label": "购买日期", "type": "date", "required": False, "reminder": False},
    ],
    "tops":  "clothing",
    "pants": "clothing",
    "shoes": "clothing",
    "bags":  "clothing",
    # ---- 其他 ----
    "other": [
        {"name": "production_date", "label": "生产日期", "type": "date",     "required": False, "reminder": False},
        {"name": "expire_date",     "label": "过期日期", "type": "date",     "required": False, "reminder": True},
        {"name": "notes",           "label": "备注",     "type": "textarea", "required": False, "reminder": False},
    ],
}


def _resolve_fields(code: str):
    """解析字段配置（支持别名引用，如 'snacks' -> 'food' 的字段）"""
    val = _CATEGORY_EXTENSION_FIELDS.get(code)
    if val is None:
        return None
    if isinstance(val, str):
        return _CATEGORY_EXTENSION_FIELDS.get(val)
    return val


def init_db():
    """初始化数据库（创建所有表 + 初始化默认数据）"""
    from models import User, Family, Item, ItemExtension, Category, Location, Reminder, ChatMessage, Feedback

    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")

    _init_categories()
    _sync_extension_fields()   # 每次启动都同步最新字段配置


def _init_categories():
    """初始化默认分类数据（仅首次，已有则跳过）"""
    import json
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
            fields = _resolve_fields(row["code"])
            cat = Category(
                code=row["code"],
                name=row["name"],
                icon=row.get("icon"),
                parent_id=parent_id,
                extension_fields=json.dumps(fields, ensure_ascii=False) if fields else None,
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


def _sync_extension_fields():
    """将 _CATEGORY_EXTENSION_FIELDS 的最新配置同步到数据库（每次启动执行）"""
    import json
    from models import Category

    db = SessionLocal()
    try:
        cats = db.query(Category).filter(Category.code.isnot(None)).all()
        updated = 0
        for cat in cats:
            fields = _resolve_fields(cat.code)
            new_val = json.dumps(fields, ensure_ascii=False) if fields else None
            if cat.extension_fields != new_val:
                cat.extension_fields = new_val
                updated += 1
        if updated:
            db.commit()
            print(f"[OK] Synced extension_fields for {updated} categories")
        else:
            print("[INFO] extension_fields already up-to-date")
    except Exception as e:
        print(f"[ERROR] Failed to sync extension_fields: {e}")
        db.rollback()
    finally:
        db.close()