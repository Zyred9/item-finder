"""
对话模型
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, BigInteger, Index
from datetime import datetime

from .base import Base


class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "chat_messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_id = Column(BigInteger, nullable=False, index=True, comment="家庭 ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户 ID")
    session_id = Column(String(36), nullable=False, index=True, comment="会话 ID")
    
    # 消息内容
    role = Column(String(20), nullable=False, comment="角色：user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    
    # AI 相关
    intent = Column(String(50), comment="意图：search/query_location/query_expire/...")
    entities = Column(Text, comment="提取的实体 (JSON)")
    matched_items = Column(Text, comment="匹配的物品 ID 列表 (JSON)")
    
    # 语音相关
    audio_path = Column(String(500), comment="语音文件路径")
    audio_duration = Column(Integer, comment="语音时长 (秒)")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    __table_args__ = (
        Index('idx_chat_family', 'family_id'),
        Index('idx_chat_user', 'user_id'),
        Index('idx_chat_session', 'session_id'),
    )
    
    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:20]}...>"
