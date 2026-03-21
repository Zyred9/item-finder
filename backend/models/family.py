"""
家庭模型
"""
import secrets
from sqlalchemy import Column, String, DateTime, BigInteger
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
    
    def __repr__(self):
        return f"<Family {self.name}>"
