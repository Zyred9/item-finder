"""
家庭服务层
"""
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from models import Family, User


class FamilyService:
    """家庭业务逻辑"""
    
    @staticmethod
    def create(db: Session, name: str, creator_id: Optional[str] = None) -> Family:
        """创建家庭"""
        family = Family(name=name)
        db.add(family)
        db.commit()
        db.refresh(family)
        
        # 如果有创建者，设为管理员
        if creator_id:
            user = db.query(User).filter(User.id == creator_id).first()
            if user:
                user.family_id = family.id
                user.is_admin = True
                db.commit()
        
        return family
    
    @staticmethod
    def get_by_id(db: Session, family_id: str) -> Optional[Family]:
        """获取家庭"""
        return db.query(Family).filter(Family.id == family_id).first()
    
    @staticmethod
    def get_by_invite_code(db: Session, invite_code: str) -> Optional[Family]:
        """通过邀请码获取家庭"""
        return db.query(Family).filter(Family.invite_code == invite_code.upper()).first()
    
    @staticmethod
    def join(db: Session, invite_code: str, user_id: str) -> tuple[bool, str]:
        """加入家庭"""
        family = FamilyService.get_by_invite_code(db, invite_code)
        if not family:
            return False, "邀请码无效"
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"
        
        if user.family_id == family.id:
            return True, "已在该家庭中"
        
        user.family_id = family.id
        db.commit()
        
        return True, family.name
    
    @staticmethod
    def get_members(db: Session, family_id: str) -> list[User]:
        """获取家庭成员"""
        return db.query(User).filter(User.family_id == family_id).all()
    
    @staticmethod
    def get_member_count(db: Session, family_id: str) -> int:
        """获取成员数量"""
        return db.query(User).filter(User.family_id == family_id).count()