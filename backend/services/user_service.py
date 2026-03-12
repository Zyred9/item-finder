"""
用户服务层
"""
from sqlalchemy.orm import Session
from typing import Optional

from models import User, Family


class UserService:
    """用户业务逻辑"""
    
    @staticmethod
    def create(db: Session, wechat_openid: str, family_id: Optional[int] = None, 
               nickname: Optional[str] = None, avatar_url: Optional[str] = None) -> User:
        """创建用户"""
        # 检查是否已存在
        existing = db.query(User).filter(User.wechat_openid == wechat_openid).first()
        if existing:
            return existing
        
        # 判断是否是家庭第一个成员（自动设为管理员）
        is_first = (family_id is None) or db.query(User).filter(User.family_id == family_id).count() == 0
        
        user = User(
            wechat_openid=wechat_openid,
            family_id=family_id,
            nickname=nickname,
            avatar_url=avatar_url,
            is_admin=is_first
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_openid(db: Session, openid: str) -> Optional[User]:
        """通过 OpenID 获取用户"""
        return db.query(User).filter(User.wechat_openid == openid).first()
    
    @staticmethod
    def update(db: Session, user_id: int, **kwargs) -> Optional[User]:
        """更新用户信息"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_family_info(db: Session, user_id: int) -> Optional[dict]:
        """获取用户所属家庭信息"""
        user = UserService.get_by_id(db, user_id)
        if not user or not user.family_id:
            return None
        
        family = db.query(Family).filter(Family.id == user.family_id).first()
        if not family:
            return None
        
        return {
            "family_id": int(family.id),
            "family_name": family.name,
            "is_admin": user.is_admin
        }