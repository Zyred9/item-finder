"""
Embedding 服务
"""
from typing import List, Dict, Any

import httpx

from config.settings import settings


class EmbeddingService:
    """调用百炼兼容接口生成向量"""

    @staticmethod
    def is_available() -> bool:
        return bool(settings.BAILIAN_API_KEY and settings.EMBEDDING_BASE_URL and settings.EMBEDDING_MODEL)

    @staticmethod
    def embed_text(text: str) -> List[float]:
        content = (text or "").strip()
        if not content:
            return []
        if not EmbeddingService.is_available():
            raise ValueError("未配置 Embedding 服务，请检查 BAILIAN_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL")

        url = f"{settings.EMBEDDING_BASE_URL.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.BAILIAN_API_KEY}",
            "Content-Type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": settings.EMBEDDING_MODEL,
            "input": content,
        }
        print(f"[embedding][request] url={url}")
        print(f"[embedding][request] chars={len(content)}")

        with httpx.Client(timeout=settings.QDRANT_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

        print(f"[embedding][response] body_keys={list(data.keys())}")
        vectors = data.get("data") or []
        if not vectors:
            raise ValueError("Embedding 返回为空")
        vector = (vectors[0] or {}).get("embedding") or []
        if not vector:
            raise ValueError("Embedding 向量为空")
        return vector
