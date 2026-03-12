"""
位置模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Location(Base):
    """常用位置表"""
    __tablename__ = "locations"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_id = Column(BigInteger, ForeignKey("families.id", ondelete="CASCADE"),
                      nullable=False, index=True, comment="家庭ID")
    name = Column(String(100), nullable=False, comment="位置名称")
    parent_id = Column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"),
                      nullable=True, index=True, comment="父位置ID")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系（自引用）
    parent = relationship("Location", remote_side=[id], backref="children")
    family = relationship("Family", back_populates="locations")
    
    def __repr__(self):
        return f"<Location {self.name}>"