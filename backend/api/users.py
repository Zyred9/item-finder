
"""
用户相关 API
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from schemas import Response
from schemas.user import UserUpdate, UserResponse
from services import UserService


router = APIRouter(prefix="/users", tags=["用户"])


def get_current_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-Id")) -> int:
    """获取当前用户ID（从请求头 X-User-Id 获取，整型）"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的用户ID")


@router.patch("/{user_id}", response_model=Response[UserResponse])
async def update_user(
    user_id: int,
    request: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    更新用户信息（家庭内部任意成员可编辑任意成员备注）
    """
    current_user = db.query(User).filter(User.id == current_user_id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="当前用户不存在")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 只能修改同一家庭内成员
    if (
        current_user.family_id is None
        or target_user.family_id is None
        or current_user.family_id != target_user.family_id
    ):
        raise HTTPException(status_code=403, detail="只能修改同一家庭内成员的信息")

    user = UserService.update(
        db,
        user_id,
        nickname=request.nickname,
        avatar_url=request.avatar_url,
        remark=request.remark,
    )

    return Response(
        data=UserResponse(
            id=int(user.id),
            family_id=int(user.family_id) if user.family_id else None,
            wechat_openid=user.wechat_openid,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin,
            created_at=user.created_at,
            remark=user.remark,
        )
    )

