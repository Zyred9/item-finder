"""
物品相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import json
from datetime import datetime

import httpx

from models import get_db
from schemas import Response
from schemas.item import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse
from services import ItemService, UserService
from config.settings import settings

router = APIRouter(prefix="/items", tags=["物品管理"])


def get_current_user(user_id: Optional[str] = Header(None, alias="X-User-Id")) -> int:
    """获取当前用户ID（整型）"""
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        return int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的用户ID")


@router.post("/photo/understand", response_model=Response[dict])
async def photo_understand(
    photo: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    """存物主图理解：拍照识物，返回建议名称与分类（Qwen-VL）"""
    from config.settings import settings
    from services.vision_service import understand_item_photo

    if not settings.BAILIAN_API_KEY:
        raise HTTPException(status_code=503, detail="未配置 BAILIAN_API_KEY（百炼）")
    ext = (photo.filename or "").rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    content = await photo.read()
    if not content:
        raise HTTPException(status_code=400, detail="图片为空")
    try:
        out = understand_item_photo(content, mime_type=mime)
        return Response(data={
            "suggested_name": out.get("suggested_name", ""),
            "suggested_category": out.get("suggested_category", ""),
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"视觉模型请求失败: {e.response.status_code}")


@router.post("/photo/ocr", response_model=Response[dict])
async def photo_ocr(
    photo: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    """扩展凭证 OCR：说明书、发票、药盒等图片提取文字（qwen-vl-ocr）"""
    from config.settings import settings
    from services.ocr_service import extract_text

    if not settings.BAILIAN_API_KEY:
        raise HTTPException(status_code=503, detail="未配置 BAILIAN_API_KEY（百炼）")
    ext = (photo.filename or "").rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    content = await photo.read()
    if not content:
        raise HTTPException(status_code=400, detail="图片为空")
    try:
        text = extract_text(content, mime_type=mime)
        return Response(data={"text": text})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"OCR 请求失败: {e.response.status_code}")


@router.post("", response_model=Response[ItemResponse])
async def create_item(
    name: str = Form(...),
    location: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),  # 前端传整型或空
    extension: Optional[str] = Form(None),  # JSON 字符串
    photo: Optional[UploadFile] = File(None),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建物品"""
    user = UserService.get_by_id(db, user_id)
    if not user or not user.family_id:
        raise HTTPException(status_code=400, detail="用户未加入家庭")
    
    # 处理照片上传
    photo_path = None
    if photo:
        ext = photo.filename.split(".")[-1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="不支持的图片格式")
        
        # 生成文件路径
        today = datetime.now()
        filename = f"{uuid.uuid4()}.{ext}"
        relative_path = f"photos/{today.year}/{today.month:02d}/{filename}"
        full_path = settings.UPLOAD_DIR / relative_path
        
        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        content = await photo.read()
        with open(full_path, "wb") as f:
            f.write(content)
        
        photo_path = f"/uploads/{relative_path}"
    
    # 解析扩展信息 JSON
    extension_data = None
    if extension:
        try:
            extension_data = json.loads(extension)
        except json.JSONDecodeError:
            pass  # 忽略无效的 JSON
    
    category_id_int = int(category_id) if category_id else None
    item = ItemService.create(
        db=db,
        family_id=int(user.family_id),
        creator_id=user_id,
        name=name,
        location=location,
        description=description,
        photo_path=photo_path,
        category_id=category_id_int,
        extension_data=extension_data
    )

    return Response(data=ItemResponse(
        id=int(item.id),
        family_id=int(item.family_id),
        creator_id=int(item.creator_id),
        creator_name=user.nickname,
        name=item.name,
        location=item.location,
        description=item.description,
        photo_path=item.photo_path,
        category_id=int(item.category_id) if item.category_id else None,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at
    ))


@router.get("/{item_id}", response_model=Response[ItemResponse])
async def get_item(
    item_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取物品详情"""
    details = ItemService.get_with_details(db, item_id)
    if not details:
        raise HTTPException(status_code=404, detail="物品不存在")

    item = details["item"]

    return Response(data=ItemResponse(
        id=int(item.id),
        family_id=int(item.family_id),
        creator_id=int(item.creator_id),
        creator_name=details["creator_name"],
        name=item.name,
        location=item.location,
        description=item.description,
        photo_path=item.photo_path,
        category_id=int(item.category_id) if item.category_id else None,
        category_name=details["category_name"],
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        extension=details["extension"]
    ))


@router.put("/{item_id}", response_model=Response[ItemResponse])
async def update_item(
    item_id: int,
    request: ItemUpdate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新物品"""
    item = ItemService.update(db, item_id, **request.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    details = ItemService.get_with_details(db, item_id)

    return Response(data=ItemResponse(
        id=int(item.id),
        family_id=int(item.family_id),
        creator_id=int(item.creator_id),
        creator_name=details["creator_name"],
        name=item.name,
        location=item.location,
        description=item.description,
        photo_path=item.photo_path,
        category_id=int(item.category_id) if item.category_id else None,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at
    ))


@router.delete("/{item_id}", response_model=Response)
async def delete_item(
    item_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除物品"""
    success = ItemService.delete(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="物品不存在")
    
    return Response(message="物品已删除")


@router.get("", response_model=Response[ItemListResponse])
async def get_family_items(
    family_id: int,
    limit: int = 50,
    offset: int = 0,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取家庭物品列表"""
    items, total = ItemService.get_by_family(db, family_id, limit, offset)

    result = []
    for item in items:
        details = ItemService.get_with_details(db, item.id)
        result.append(ItemResponse(
            id=int(item.id),
            family_id=int(item.family_id),
            creator_id=int(item.creator_id),
            creator_name=details["creator_name"],
            name=item.name,
            location=item.location,
            description=item.description,
            photo_path=item.photo_path,
            category_id=int(item.category_id) if item.category_id else None,
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))

    return Response(data=ItemListResponse(total=total, items=result))


@router.get("/search", response_model=Response[ItemListResponse])
async def search_items(
    q: str,
    family_id: int,
    limit: int = 20,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索物品"""
    items = ItemService.search(db, family_id, q, limit)

    result = []
    for item in items:
        details = ItemService.get_with_details(db, item.id)
        result.append(ItemResponse(
            id=int(item.id),
            family_id=int(item.family_id),
            creator_id=int(item.creator_id),
            creator_name=details["creator_name"],
            name=item.name,
            location=item.location,
            description=item.description,
            photo_path=item.photo_path,
            category_id=int(item.category_id) if item.category_id else None,
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))

    return Response(data=ItemListResponse(total=len(result), items=result))