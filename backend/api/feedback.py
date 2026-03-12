"""
帮助与反馈 API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db, Feedback
from schemas import Response
from schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["帮助与反馈"])


def get_current_user_id(user_id: Optional[str] = Header(None, alias="X-User-Id")) -> int:
    """获取当前用户ID"""
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        return int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的用户ID")


@router.post("", response_model=Response[FeedbackResponse])
async def submit_feedback(
    body: FeedbackCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """提交帮助与反馈，写入数据库"""
    feedback = Feedback(
        user_id=user_id,
        content=body.content.strip(),
        contact=body.contact.strip() if body.contact else None,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return Response(
        data=FeedbackResponse(
            id=int(feedback.id),
            content=feedback.content,
            contact=feedback.contact,
            created_at=feedback.created_at,
        )
    )
