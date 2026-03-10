"""
家庭模型
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Family(Base):
    """家庭表"""
    __tablename__ = "families"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, comment="家庭名称")
    invite_code = Column(String(6), unique=True, nullable=False, 
                         default=lambda: str(uuid.uuid4())[:6].upper(),
                         comment="邀请码")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关系
    users = relationship("User", back_populates="family", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="family", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="family", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="family", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="family", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Family {self.name}>"