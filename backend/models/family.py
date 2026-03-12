"""
家庭模型
"""
import secrets
from sqlalchemy import Column, String, DateTime, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


def _default_invite_code():
    return secrets.token_hex(3).upper()


class Family(Base):
    """家庭表"""
    __tablename__ = "families"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="家庭名称")
    invite_code = Column(String(6), unique=True, nullable=False,
                        default=_default_invite_code,
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