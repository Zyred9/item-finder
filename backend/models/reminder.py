"""
提醒模型
"""
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Reminder(Base):
    """智能提醒表"""
    __tablename__ = "reminders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    family_id = Column(String(36), ForeignKey("families.id", ondelete="CASCADE"), 
                       nullable=False, index=True, comment="家庭ID")
    item_id = Column(String(36), ForeignKey("items.id", ondelete="CASCADE"), 
                     nullable=False, index=True, comment="物品ID")
    
    # 提醒信息
    type = Column(String(20), nullable=False, index=True, 
                  comment="类型: expire/open/warranty/document/custom")
    level = Column(String(20), default="normal", index=True, 
                   comment="级别: urgent/warning/normal")
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, comment="内容")
    
    # 时间
    remind_at = Column(Date, nullable=False, index=True, comment="提醒日期")
    triggered_at = Column(DateTime, comment="触发时间")
    
    # 状态
    status = Column(String(20), default="pending", index=True, 
                    comment="状态: pending/done/ignored/deferred")
    deferred_to = Column(Date, comment="延期到")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    family = relationship("Family", back_populates="reminders")
    item = relationship("Item", back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder {self.title}>"