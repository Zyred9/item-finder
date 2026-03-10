"""
物品模型
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Item(Base):
    """物品表"""
    __tablename__ = "items"
    
    # 基础信息
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    family_id = Column(String(36), ForeignKey("families.id", ondelete="CASCADE"), 
                       nullable=False, index=True, comment="家庭ID")
    creator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), 
                        nullable=False, index=True, comment="创建者ID")
    name = Column(String(100), nullable=False, index=True, comment="物品名称")
    location = Column(String(200), nullable=False, comment="存放位置")
    description = Column(Text, comment="描述")
    photo_path = Column(String(500), comment="照片路径")
    
    # 分类
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="SET NULL"),
                         index=True, comment="分类ID")
    
    # 状态
    status = Column(String(20), default="active", index=True, comment="状态: active/archived/deleted")
    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    
    # 统计
    find_count = Column(Integer, default=0, comment="查找次数")
    last_found_at = Column(DateTime, comment="最后查找时间")
    
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
    """物品扩展信息表"""
    __tablename__ = "item_extensions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String(36), ForeignKey("items.id", ondelete="CASCADE"), 
                     unique=True, nullable=False, comment="物品ID")
    
    # 药品相关
    expire_date = Column(Date, index=True, comment="过期日期")
    production_date = Column(Date, comment="生产日期")
    shelf_life_days = Column(Integer, comment="保质期(天)")
    open_date = Column(Date, comment="开封日期")
    open_shelf_life = Column(Integer, comment="开封后保质期(天)")
    dosage = Column(Text, comment="用法用量")
    
    # 证件相关
    document_number = Column(String(100), comment="证件号码(加密)")
    issuer = Column(String(200), comment="发证机关")
    
    # 电器相关
    brand = Column(String(100), comment="品牌")
    model = Column(String(100), comment="型号")
    purchase_date = Column(Date, comment="购买日期")
    warranty_date = Column(Date, index=True, comment="保修到期日")
    accessories = Column(Text, comment="配件清单(JSON)")
    
    # 衣物相关
    size = Column(String(20), comment="尺码")
    color = Column(String(50), comment="颜色")
    season = Column(String(20), comment="季节")
    material = Column(String(100), comment="材质")
    
    # 食品相关
    storage_condition = Column(String(50), comment="储存条件")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    item = relationship("Item", back_populates="extension")
    
    def __repr__(self):
        return f"<ItemExtension for {self.item_id}>"