"""
用户模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_id = Column(BigInteger, ForeignKey("families.id", ondelete="SET NULL"),
                      nullable=True, index=True, comment="家庭ID")
    wechat_openid = Column(String(64), unique=True, nullable=False, comment="微信OpenID")
    nickname = Column(String(50), comment="昵称")
    remark = Column(String(100), nullable=True, comment="家庭内备注名")
    avatar_url = Column(String(500), comment="头像URL")
    is_admin = Column(Boolean, default=False, comment="是否管理员")
    created_at = Column(DateTime, default=datetime.now, comment="加入时间")
    
    # 关系
    family = relationship("Family", back_populates="users")
    items = relationship("Item", back_populates="creator", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.nickname or self.id}>"