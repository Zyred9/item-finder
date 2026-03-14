"""
搜索索引补偿 worker
"""
from models.base import SessionLocal
from services.search_index_service import SearchIndexService


def run_once(db=None, limit: int = 20) -> int:
    if db is not None:
        return SearchIndexService.process_pending_tasks(db, limit=limit)

    local_db = SessionLocal()
    try:
        return SearchIndexService.process_pending_tasks(local_db, limit=limit)
    finally:
        local_db.close()


if __name__ == "__main__":
    processed = run_once()
    print(f"[search-sync-worker] processed={processed}")
