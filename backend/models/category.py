"""
分类模型
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Category(Base):
    """物品分类表"""
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, comment="分类名称")
    icon = Column(String(10), comment="图标(emoji)")
    parent_id = Column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), 
                       index=True, comment="父分类ID")
    sort_order = Column(Integer, default=0, comment="排序")
    extension_fields = Column(Text, comment="扩展字段配置(JSON)")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系（自引用）
    parent = relationship("Category", remote_side=[id], backref="children")
    items = relationship("Item", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"