"""
对话模型
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    family_id = Column(String(36), ForeignKey("families.id", ondelete="CASCADE"), 
                       nullable=False, index=True, comment="家庭ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), 
                     nullable=False, index=True, comment="用户ID")
    session_id = Column(String(36), nullable=False, index=True, comment="会话ID")
    
    # 消息内容
    role = Column(String(20), nullable=False, comment="角色: user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    
    # AI 相关
    intent = Column(String(50), comment="意图: search/query_location/query_expire/...")
    entities = Column(Text, comment="提取的实体(JSON)")
    matched_items = Column(Text, comment="匹配的物品ID列表(JSON)")
    
    # 语音相关
    audio_path = Column(String(500), comment="语音文件路径")
    audio_duration = Column(Integer, comment="语音时长(秒)")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # 关系
    family = relationship("Family", back_populates="chat_messages")
    user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:20]}...>"