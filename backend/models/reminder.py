"""
提醒模型
"""
from sqlalchemy import Column, String, Date, DateTime, Text, BigInteger, Index
from datetime import datetime

from .base import Base


class Reminder(Base):
    """智能提醒表"""
    __tablename__ = "reminders"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_id = Column(BigInteger, nullable=False, index=True, comment="家庭 ID")
    item_id = Column(BigInteger, nullable=False, index=True, comment="物品 ID")
    
    # 提醒信息
    type = Column(String(20), nullable=False, index=True, 
                  comment="类型：expire/open/warranty/document/custom")
    level = Column(String(20), default="normal", index=True, 
                   comment="级别：urgent/warning/normal")
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, comment="内容")
    
    # 时间
    remind_at = Column(Date, nullable=False, index=True, comment="提醒日期")
    triggered_at = Column(DateTime, comment="触发时间")
    
    # 状态
    status = Column(String(20), default="pending", index=True, 
                    comment="状态：pending/done/ignored/deferred")
    deferred_to = Column(Date, comment="延期到")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_reminder_family', 'family_id'),
        Index('idx_reminder_item', 'item_id'),
    )
    
    def __repr__(self):
        return f"<Reminder {self.title}>"
