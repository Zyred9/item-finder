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
        
        # 创建扩展信息
        if extension_data:
            extension = ItemExtension(item_id=item.id, **extension_data)
            db.add(extension)

        db.commit()
        db.refresh(item)
        sync_reminders_for_item(db, item)

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
        
        return {
            "item": item,
            "creator_name": creator.nickname if creator else None,
            "category_name": category.name if category else None,
            "extension": item.extension
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
        
        # 更新扩展信息
        if extension_data:
            if item.extension:
                for key, value in extension_data.items():
                    if hasattr(item.extension, key):
                        setattr(item.extension, key, value)
            else:
                extension = ItemExtension(item_id=item.id, **extension_data)
                db.add(extension)
        
        item.updated_at = datetime.now()
        db.commit()
        db.refresh(item)
        sync_reminders_for_item(db, item)

        return item
    
    @staticmethod
    def delete(db: Session, item_id: int) -> bool:
        """删除物品"""
        item = ItemService.get_by_id(db, item_id)
        if not item:
            return False
        
        db.delete(item)
        db.commit()
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
        """搜索物品"""
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
        """记录查找（增加查找次数）"""
        item = ItemService.get_by_id(db, item_id)
        if not item:
            return None
        
        item.find_count += 1
        item.last_found_at = datetime.now()
        db.commit()
        db.refresh(item)
        
        return item