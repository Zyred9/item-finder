"""
Qdrant 搜索索引服务
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session, joinedload

from config.settings import settings
from models import Item, SearchSyncTask
from services.embedding_service import EmbeddingService


class SearchIndexService:
    """负责构建搜索文档、同步 Qdrant、处理补偿任务"""

    EXTENSION_LABELS = {
        "expire_date": "过期日期",
        "production_date": "生产日期",
        "shelf_life_days": "保质期天数",
        "warranty_date": "保修到期日",
    }

    @staticmethod
    def is_enabled() -> bool:
        return bool(settings.QDRANT_URL and EmbeddingService.is_available())

    @staticmethod
    def _headers() -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if settings.QDRANT_API_KEY:
            headers["api-key"] = settings.QDRANT_API_KEY
        return headers

    @staticmethod
    def _collection_url() -> str:
        return f"{settings.QDRANT_URL.rstrip('/')}/collections/{settings.QDRANT_COLLECTION}"

    @staticmethod
    def _point_payload(item: Item, category_name: str, creator_name: str, search_text: str) -> Dict[str, Any]:
        return {
            "item_id": int(item.id),
            "family_id": int(item.family_id),
            "status": item.status,
            "name": item.name,
            "location": item.location,
            "description": item.description or "",
            "photo_path": item.photo_path or "",
            "category_name": category_name or "",
            "creator_name": creator_name or "",
            "search_text": search_text,
            "updated_at": item.updated_at.isoformat() if item.updated_at else "",
        }

    @staticmethod
    def build_search_document(item: Item, category_name: str = "", creator_name: str = "") -> str:
        parts: List[str] = [
            f"物品名称：{item.name}",
            f"存放位置：{item.location}",
        ]
        if item.description:
            parts.append(f"物品描述：{item.description}")
        if category_name:
            parts.append(f"物品分类：{category_name}")
        if creator_name:
            parts.append(f"创建者：{creator_name}")

        extension = getattr(item, "extension", None)
        if extension:
            for field_name, field_label in SearchIndexService.EXTENSION_LABELS.items():
                value = getattr(extension, field_name, None)
                if value not in (None, "", []):
                    parts.append(f"{field_label}：{value}")

        return "\n".join(parts)

    @staticmethod
    def _load_item(db: Session, item_id: int) -> Optional[Item]:
        return db.query(Item).filter(Item.id == item_id).first()

    @staticmethod
    def ensure_collection() -> None:
        if not settings.QDRANT_URL:
            raise ValueError("未配置 QDRANT_URL")
        body = {
            "vectors": {
                "size": settings.EMBEDDING_VECTOR_SIZE,
                "distance": "Cosine",
            }
        }
        with httpx.Client(timeout=settings.QDRANT_TIMEOUT_SECONDS) as client:
            response = client.put(
                SearchIndexService._collection_url(),
                json=body,
                headers=SearchIndexService._headers(),
            )
            if response.status_code == 409:
                return
            if response.status_code not in (200, 201):
                response.raise_for_status()

    @staticmethod
    def upsert_item(db: Session, item_id: int) -> None:
        item = SearchIndexService._load_item(db, item_id)
        if not item:
            raise ValueError(f"物品不存在: {item_id}")

        category_name = item.category.name if getattr(item, "category", None) else ""
        creator_name = item.creator.nickname if getattr(item, "creator", None) else ""
        search_text = SearchIndexService.build_search_document(item, category_name=category_name, creator_name=creator_name)
        vector = EmbeddingService.embed_text(search_text)
        SearchIndexService.ensure_collection()
        body = {
            "points": [
                {
                    "id": int(item.id),
                    "vector": vector,
                    "payload": SearchIndexService._point_payload(item, category_name, creator_name, search_text),
                }
            ]
        }
        with httpx.Client(timeout=settings.QDRANT_TIMEOUT_SECONDS) as client:
            response = client.put(
                f"{SearchIndexService._collection_url()}/points?wait=true",
                json=body,
                headers=SearchIndexService._headers(),
            )
            response.raise_for_status()
        print(f"[search-index] upsert success item_id={item_id}")

    @staticmethod
    def delete_item(item_id: int) -> None:
        if not settings.QDRANT_URL:
            raise ValueError("未配置 QDRANT_URL")
        SearchIndexService.ensure_collection()
        body = {"points": [int(item_id)]}
        with httpx.Client(timeout=settings.QDRANT_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{SearchIndexService._collection_url()}/points/delete?wait=true",
                json=body,
                headers=SearchIndexService._headers(),
            )
            response.raise_for_status()
        print(f"[search-index] delete success item_id={item_id}")

    @staticmethod
    def search_points(query_vector: List[float], family_id: int, limit: int) -> List[Dict[str, Any]]:
        if not settings.QDRANT_URL:
            return []
        body = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "family_id", "match": {"value": int(family_id)}},
                    {"key": "status", "match": {"value": "active"}},
                ]
            },
        }
        with httpx.Client(timeout=settings.QDRANT_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{SearchIndexService._collection_url()}/points/search",
                json=body,
                headers=SearchIndexService._headers(),
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()

        result = []
        for point in data.get("result") or []:
            point_id = point.get("id")
            if point_id is None:
                continue
            result.append({
                "id": int(point_id),
                "score": float(point.get("score") or 0),
                "payload": point.get("payload") or {},
            })
        return result

    @staticmethod
    def create_sync_task(db: Session, item_id: int, op_type: str) -> Optional[SearchSyncTask]:
        if not SearchIndexService.is_enabled():
            return None
        task = SearchSyncTask(item_id=item_id, op_type=op_type, status="pending")
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def _calc_next_retry_at(retry_count: int) -> datetime:
        delay_minutes = min(2 ** max(retry_count - 1, 0), 60)
        return datetime.now() + timedelta(minutes=delay_minutes)

    @staticmethod
    def process_task(db: Session, task: SearchSyncTask) -> bool:
        try:
            if task.op_type == "delete":
                SearchIndexService.delete_item(task.item_id)
            else:
                SearchIndexService.upsert_item(db, task.item_id)
            task.status = "success"
            task.last_error = None
            task.next_retry_at = None
            db.commit()
            return True
        except Exception as err:
            task.status = "failed"
            task.retry_count += 1
            task.last_error = str(err)
            task.next_retry_at = SearchIndexService._calc_next_retry_at(task.retry_count)
            db.commit()
            print(f"[search-index] sync failed item_id={task.item_id} op={task.op_type} error={err}")
            return False

    @staticmethod
    def schedule_sync(db: Session, item_id: int, op_type: str) -> bool:
        task = SearchIndexService.create_sync_task(db, item_id, op_type)
        if not task:
            return False
        return SearchIndexService.process_task(db, task)

    @staticmethod
    def process_pending_tasks(db: Session, limit: int = 20) -> int:
        if not SearchIndexService.is_enabled():
            return 0
        now = datetime.now()
        tasks = db.query(SearchSyncTask).filter(
            SearchSyncTask.status.in_(("pending", "failed")),
            ((SearchSyncTask.next_retry_at.is_(None)) | (SearchSyncTask.next_retry_at <= now)),
        ).order_by(SearchSyncTask.created_at.asc()).limit(limit).all()
        processed = 0
        for task in tasks:
            SearchIndexService.process_task(db, task)
            processed += 1
        return processed
