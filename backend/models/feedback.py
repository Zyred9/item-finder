"""
用户反馈模型
"""
from sqlalchemy import Column, String, Text, DateTime, BigInteger, Index
from datetime import datetime

from .base import Base


class Feedback(Base):
    """用户反馈表"""
    __tablename__ = "feedbacks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户 ID")
    content = Column(Text, nullable=False, comment="反馈内容")
    contact = Column(String(100), nullable=True, comment="联系方式（选填）")
    created_at = Column(DateTime, default=datetime.now, comment="提交时间")

    __table_args__ = (
        Index('idx_feedback_user', 'user_id'),
    )

    def __repr__(self):
        return f"<Feedback id={self.id} user_id={self.user_id}>"
