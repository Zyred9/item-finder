"""
搜索索引同步任务模型
"""
from datetime import datetime

from sqlalchemy import Column, String, DateTime, BigInteger, Integer, Text

from .base import Base


class SearchSyncTask(Base):
    """MySQL -> Qdrant 搜索索引同步任务"""

    __tablename__ = "search_sync_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_id = Column(BigInteger, nullable=False, index=True, comment="物品ID")
    op_type = Column(String(20), nullable=False, comment="操作类型: upsert/delete")
    status = Column(String(20), default="pending", index=True, comment="任务状态: pending/success/failed")
    retry_count = Column(Integer, default=0, nullable=False, comment="重试次数")
    last_error = Column(Text, comment="最后一次错误信息")
    next_retry_at = Column(DateTime, index=True, comment="下次重试时间")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<SearchSyncTask item_id={self.item_id} op={self.op_type} status={self.status}>"
