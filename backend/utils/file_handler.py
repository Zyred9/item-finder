"""
文件处理工具
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from config.settings import settings


async def save_upload_file(
    file: UploadFile, 
    sub_dir: str = "photos",
    allowed_extensions: Optional[set] = None
) -> str:
    """
    保存上传文件
    
    Args:
        file: 上传的文件
        sub_dir: 子目录
        allowed_extensions: 允许的扩展名
    
    Returns:
        文件相对路径
    """
    if not allowed_extensions:
        allowed_extensions = settings.ALLOWED_EXTENSIONS
    
    # 检查扩展名
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in allowed_extensions:
        raise ValueError(f"不支持的文件格式: {ext}")
    
    # 生成文件名
    filename = f"{uuid.uuid4()}.{ext}"
    
    # 生成路径
    from datetime import datetime
    today = datetime.now()
    relative_path = f"{sub_dir}/{today.year}/{today.month:02d}/{filename}"
    full_path = settings.UPLOAD_DIR / relative_path
    
    # 确保目录存在
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    content = await file.read()
    with open(full_path, "wb") as f:
        f.write(content)
    
    return f"/uploads/{relative_path}"