"""
家庭服务层
"""
from sqlalchemy.orm import Session
from typing import Optional

from models import Family, User


class FamilyService:
    """家庭业务逻辑"""
    
    @staticmethod
    def create(db: Session, name: str, creator_id: Optional[int] = None) -> Family:
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
    def get_by_id(db: Session, family_id: int) -> Optional[Family]:
        """获取家庭"""
        return db.query(Family).filter(Family.id == family_id).first()
    
    @staticmethod
    def get_by_invite_code(db: Session, invite_code: str) -> Optional[Family]:
        """通过邀请码获取家庭"""
        return db.query(Family).filter(Family.invite_code == invite_code.upper()).first()
    
    @staticmethod
    def join(db: Session, invite_code: str, user_id: int) -> tuple[bool, str]:
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
    def get_members(db: Session, family_id: int) -> list[User]:
        """获取家庭成员"""
        return db.query(User).filter(User.family_id == family_id).all()
    
    @staticmethod
    def get_member_count(db: Session, family_id: int) -> int:
        """获取成员数量"""
        return db.query(User).filter(User.family_id == family_id).count()
    
    @staticmethod
    def remove_member(db: Session, family_id: int, member_id: int, operator_id: int) -> tuple[bool, str]:
        """
        删除家庭成员
        
        Args:
            db: 数据库会话
            family_id: 家庭 ID
            member_id: 要删除的成员 ID
            operator_id: 操作者 ID（必须是管理员）
        
        Returns:
            (成功标志，消息)
        """
        # 验证操作者是否为管理员
        operator = db.query(User).filter(User.id == operator_id).first()
        if not operator or not operator.is_admin:
            return False, "只有管理员可以删除成员"
        
        # 验证成员是否存在
        member = db.query(User).filter(User.id == member_id).first()
        if not member:
            return False, "成员不存在"
        
        # 验证成员是否属于该家庭
        if member.family_id != family_id:
            return False, "成员不属于该家庭"
        
        # 不能删除自己
        if member.id == operator_id:
            return False, "不能删除自己"
        
        # 不能删除其他管理员
        if member.is_admin:
            return False, "不能删除管理员"
        
        # 删除成员（将其家庭 ID 置为 NULL）
        member.family_id = None
        member.is_admin = False
        db.commit()
        
        return True, "删除成功"