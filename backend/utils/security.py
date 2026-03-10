"""
安全相关工具
"""
import uuid


def generate_uuid() -> str:
    """生成 UUID"""
    return str(uuid.uuid4())