"""
家庭相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db, Family
from schemas import Response
from schemas.family import FamilyCreate, FamilyResponse, FamilyJoinRequest
from schemas.user import UserCreate, UserResponse
from services import FamilyService, UserService

router = APIRouter(prefix="/families", tags=["家庭管理"])


def get_current_user(user_id: Optional[str] = Header(None, alias="X-User-Id")) -> str:
    """获取当前用户ID"""
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")
    return user_id


@router.post("", response_model=Response[FamilyResponse])
async def create_family(
    request: FamilyCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建家庭"""
    family = FamilyService.create(db, request.name, user_id)
    
    # 更新用户家庭关联
    user = UserService.get_by_id(db, user_id)
    if user:
        user.family_id = family.id
        user.is_admin = True
        db.commit()
    
    return Response(data=FamilyResponse(
        id=family.id,
        name=family.name,
        invite_code=family.invite_code,
        member_count=1,
        created_at=family.created_at
    ))


@router.post("/join", response_model=Response[dict])
async def join_family(
    request: FamilyJoinRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """加入家庭"""
    success, result = FamilyService.join(db, request.invite_code, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=result)
    
    return Response(data={
        "family_id": FamilyService.get_by_invite_code(db, request.invite_code).id,
        "family_name": result
    })


@router.get("/{family_id}", response_model=Response[FamilyResponse])
async def get_family(
    family_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取家庭信息"""
    family = FamilyService.get_by_id(db, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="家庭不存在")
    
    member_count = FamilyService.get_member_count(db, family_id)
    
    return Response(data=FamilyResponse(
        id=family.id,
        name=family.name,
        invite_code=family.invite_code,
        member_count=member_count,
        created_at=family.created_at
    ))


@router.get("/{family_id}/members", response_model=Response[list[UserResponse]])
async def get_family_members(
    family_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取家庭成员"""
    members = FamilyService.get_members(db, family_id)
    
    return Response(data=[
        UserResponse(
            id=m.id,
            family_id=m.family_id,
            wechat_openid=m.wechat_openid,
            nickname=m.nickname,
            avatar_url=m.avatar_url,
            is_admin=m.is_admin,
            created_at=m.created_at
        ) for m in members
    ])