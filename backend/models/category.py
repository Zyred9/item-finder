"""
分类模型
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, BigInteger
from datetime import datetime

from .base import Base


class Category(Base):
    """物品分类表（只保留一级分类，共 7 个）"""
    __tablename__ = "categories"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=True, index=True, comment="业务编码，如 food/medicine")
    name = Column(String(50), nullable=False, comment="分类名称")
    icon = Column(String(10), comment="图标 (emoji)")
    sort_order = Column(Integer, default=0, comment="排序")
    extension_fields = Column(Text, comment="扩展字段配置 (JSON)")
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Category {self.name}>"
