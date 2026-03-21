"""
物品服务层
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime

from models import Item, ItemExtension, User, Category
from services.expiry_reminder_agent import sync_reminders_for_item


class ItemService:
    """物品业务逻辑"""
    
    @staticmethod
    def create(db: Session, family_id: int, creator_id: int, name: str,
               location: str, description: Optional[str] = None,
               photo_path: Optional[str] = None, category_id: Optional[int] = None,
               extension_data: Optional[dict] = None) -> Item:
        """创建物品"""
        item = Item(
            family_id=family_id,
            creator_id=creator_id,
            name=name,
            location=location,
            description=description,
            photo_path=photo_path,
            category_id=category_id
        )
        db.add(item)
        db.flush()  # 获取 item.id
        
        # 创建扩展信息（空字符串转 None，避免 MySQL DATE 列报错）
        if extension_data:
            clean = {k: (None if v == '' else v) for k, v in extension_data.items()}
            extension = ItemExtension(item_id=item.id, **clean)
            db.add(extension)

        db.commit()
        db.refresh(item)
        sync_reminders_for_item(db, item)
        ItemService._schedule_search_index_sync(db, int(item.id), "upsert")

        return item
    
    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[Item]:
        """获取物品"""
        return db.query(Item).filter(Item.id == item_id).first()

    @staticmethod
    def get_by_ids(db: Session, item_ids: list) -> List[Item]:
        """根据 id 列表批量获取物品"""
        if not item_ids:
            return []
        return db.query(Item).filter(Item.id.in_(item_ids)).all()

    @staticmethod
    def get_with_details(db: Session, item_id: int) -> Optional[dict]:
        """获取物品详情（含扩展信息和创建者）"""
        item = ItemService.get_by_id(db, item_id)
        if not item:
            return None
        
        # 获取创建者
        creator = db.query(User).filter(User.id == item.creator_id).first()
        
        # 获取分类
        category = None
        if item.category_id:
            category = db.query(Category).filter(Category.id == item.category_id).first()
        
        # 获取扩展信息
        extension = db.query(ItemExtension).filter(ItemExtension.item_id == item.id).first()
        
        return {
            "item": item,
            "creator_name": creator.nickname if creator else None,
            "category_name": category.name if category else None,
            "extension": extension
        }
    
    @staticmethod
    def update(db: Session, item_id: int, **kwargs) -> Optional[Item]:
        """更新物品"""
        item = ItemService.get_by_id(db, item_id)
        if not item:
            return None
        
        extension_data = kwargs.pop("extension", None)
        
        for key, value in kwargs.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)
        
        # 更新扩展信息（空字符串转 None，避免 MySQL DATE 列报错）
        if extension_data:
            clean_ext = {k: (None if v == '' else v) for k, v in extension_data.items()}
            extension = db.query(ItemExtension).filter(ItemExtension.item_id == item.id).first()
            if extension:
                for key, value in clean_ext.items():
                    if hasattr(extension, key):
                        setattr(extension, key, value)
            else:
                extension = ItemExtension(item_id=item.id, **clean_ext)
                db.add(extension)
        
        item.updated_at = datetime.now()
        db.commit()
        db.refresh(item)
        sync_reminders_for_item(db, item)
        ItemService._schedule_search_index_sync(db, int(item.id), "upsert")

        return item
    
    @staticmethod
    def delete(db: Session, item_id: int) -> bool:
        """删除物品（同时删除相关提醒）"""
        item = ItemService.get_by_id(db, item_id)
        if not item:
            return False
        
        from models import Reminder
        
        # 先删除相关提醒（确保级联删除）
        db.query(Reminder).filter(Reminder.item_id == item.id).delete()
        
        deleted_item_id = int(item.id)
        db.delete(item)
        db.commit()
        ItemService._schedule_search_index_sync(db, deleted_item_id, "delete")
        
        return True
    
    @staticmethod
    def get_by_family(db: Session, family_id: int, limit: int = 50,
                      offset: int = 0) -> tuple[List[Item], int]:
        """获取家庭物品列表"""
        query = db.query(Item).filter(
            Item.family_id == family_id,
            Item.status == "active"
        ).order_by(Item.created_at.desc())
        
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        
        return items, total
    
    @staticmethod
    def search(db: Session, family_id: int, keyword: str,
               limit: int = 20) -> List[Item]:
        """搜索物品（优先语义搜索，失败时回退 MySQL 模糊匹配）"""
        from services.semantic_search_service import SemanticSearchService

        items, _ = SemanticSearchService.search_items(db, family_id, keyword, limit)
        return items

    @staticmethod
    def search_by_keyword(db: Session, family_id: int, keyword: str,
                          limit: int = 20) -> List[Item]:
        """MySQL 关键词模糊搜索兜底"""
        return db.query(Item).filter(
            Item.family_id == family_id,
            Item.status == "active",
            or_(
                Item.name.contains(keyword),
                Item.location.contains(keyword),
                Item.description.contains(keyword)
            )
        ).order_by(Item.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def record_find(db: Session, item_id: int) -> Optional[Item]:
        """记录查找（字段已清理，仅做查找并返回）"""
        return ItemService.get_by_id(db, item_id)

    @staticmethod
    def _schedule_search_index_sync(db: Session, item_id: int, op_type: str) -> None:
        from services.search_index_service import SearchIndexService

        try:
            SearchIndexService.schedule_sync(db, item_id, op_type)
        except Exception as err:
            print(f"[search-index] schedule failed item_id={item_id} op={op_type} error={err}")