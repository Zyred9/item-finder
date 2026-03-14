"""
物品模型
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, BigInteger, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Item(Base):
    """物品表"""
    __tablename__ = "items"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_id = Column(BigInteger, ForeignKey("families.id", ondelete="CASCADE"),
                      nullable=False, index=True, comment="家庭 ID")
    creator_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
                       nullable=False, index=True, comment="创建者 ID")
    category_id = Column(BigInteger, ForeignKey("categories.id", ondelete="SET NULL"),
                        nullable=True, index=True, comment="分类 ID")
    
    # 基本信息
    name = Column(String(200), nullable=False, comment="物品名称")
    location = Column(String(200), nullable=False, comment="存放位置")
    description = Column(Text, comment="描述")
    photo_path = Column(String(500), comment="照片路径")
    
    # 状态
    status = Column(String(20), default="active", index=True, comment="状态：active/archived/deleted")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关系
    family = relationship("Family", back_populates="items")
    creator = relationship("User", back_populates="items")
    category = relationship("Category", back_populates="items")
    extension = relationship("ItemExtension", back_populates="item", uselist=False, 
                            cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Item {self.name}>"


class ItemExtension(Base):
    """物品扩展信息表（只保留核心字段）"""
    __tablename__ = "item_extensions"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_id = Column(BigInteger, ForeignKey("items.id", ondelete="CASCADE"),
                    unique=True, nullable=False, index=True, comment="物品 ID")
    
    # 核心字段：过期相关（食品、药品）
    expire_date = Column(Date, index=True, comment="过期日期")
    production_date = Column(Date, comment="生产日期")
    shelf_life_days = Column(Integer, comment="保质期 (天)")
    
    # 常用字段：电器保修
    warranty_date = Column(Date, index=True, comment="保修到期日")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    item = relationship("Item", back_populates="extension")
    
    def __repr__(self):
        return f"<ItemExtension for {self.item_id}>"
