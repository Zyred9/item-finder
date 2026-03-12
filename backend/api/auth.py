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
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Response[LoginResponse])
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    微信登录
    
    - 前端传入微信登录 code
    - 后端换取 openid 并返回用户信息
    """
    # TODO: 生产环境调用微信 jscode2session 用 code 换 openid，实现「一个微信账号 = 一个用户」。
    #
    # 开发阶段：用 openid 绑定用户。清空缓存后前端会发固定 code，后端也映射到同一 openid，
    # 这样不会每次变成新用户、也不会再要求填邀请码。
    if settings.DEBUG:
        # 开发环境：统一映射到固定调试账号（不依赖 code 是否被清空）
        openid = "dev_user_fixed"
    elif request.code == "mock_dev_fixed_user":
        # 前端清空缓存后发固定 code，与 DEBUG 下账号一致，避免重新填邀请码
        openid = "dev_user_fixed"
    elif request.code.startswith("mock_"):
        # 其他 mock_xxx：用 code 本身当 openid（历史兼容）
        openid = request.code
    else:
        # 真实微信 code：生产应调 jscode2session；此处用哈希占位
        openid = f"dev_user_{hashlib.md5(request.code.encode()).hexdigest()[:8]}"
    
    # 查找用户
    user = UserService.get_by_openid(db, openid)
    
    if not user:
        # 新用户，创建临时用户记录（还没有家庭），头像和昵称从微信拉取
        user = User(
            wechat_openid=openid,
            nickname=request.nickname or f"用户{openid[-6:]}",
            avatar_url=request.avatar_url,
            family_id=None,
            is_admin=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return Response(data=LoginResponse(
            user_id=int(user.id),
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            family_id=None,
            family_name=None,
            openid=openid
        ))

    # 老用户：用微信拉取的昵称/头像更新（仅登录时同步，不支持在别处修改）
    if request.nickname is not None or request.avatar_url is not None:
        if request.nickname is not None:
            user.nickname = request.nickname
        if request.avatar_url is not None:
            user.avatar_url = request.avatar_url
        db.commit()
        db.refresh(user)

    family_info = UserService.get_family_info(db, user.id) if user.family_id else None

    return Response(data=LoginResponse(
        user_id=int(user.id),
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        family_id=family_info.get("family_id") if family_info else None,
        family_name=family_info.get("family_name") if family_info else None
    ))