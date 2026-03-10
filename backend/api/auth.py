"""
认证相关 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import hashlib

from models import get_db, User
from schemas import Response
from schemas.user import LoginRequest, LoginResponse
from services import UserService, FamilyService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Response[LoginResponse])
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    微信登录
    
    - 前端传入微信登录 code
    - 后端换取 openid 并返回用户信息
    """
    # TODO: 实际调用微信 API 换取 openid
    # 开发环境：用固定 openid 模拟（避免每次 code 不同导致创建新用户）
    # 生产环境：调用微信 API jscode2session
    if request.code.startswith("mock_"):
        # 如果前端传入的是 mock_xxx 格式，直接用后面的部分作为 openid
        openid = request.code
    else:
        # 真实微信登录时，code 是临时的，需要调用微信 API 换取真正的 openid
        # 这里暂时用 code 的哈希模拟固定用户（开发测试用）
        openid = f"dev_user_{hashlib.md5(request.code.encode()).hexdigest()[:8]}"
    
    # 查找用户
    user = UserService.get_by_openid(db, openid)
    
    if not user:
        # 新用户，创建临时用户记录（还没有家庭）
        user = User(
            wechat_openid=openid,
            nickname=f"用户{openid[-6:]}",
            family_id=None,
            is_admin=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return Response(data=LoginResponse(
            user_id=user.id,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            family_id=None,
            family_name=None,
            openid=openid
        ))
    
    # 获取家庭信息
    family_info = UserService.get_family_info(db, user.id) if user.family_id else None
    
    return Response(data=LoginResponse(
        user_id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        family_id=family_info.get("family_id") if family_info else None,
        family_name=family_info.get("family_name") if family_info else None
    ))