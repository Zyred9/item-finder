"""
全量重建搜索索引
"""
from models import Item
from models.base import SessionLocal
from services.search_index_service import SearchIndexService


def run(limit: int | None = None) -> int:
    db = SessionLocal()
    try:
        if not SearchIndexService.is_enabled():
            print("[rebuild-search-index] skipped: semantic search not configured")
            return 0

        query = db.query(Item).filter(Item.status == "active").order_by(Item.id.asc())
        if limit is not None:
            query = query.limit(limit)
        items = query.all()

        success_count = 0
        for item in items:
            try:
                SearchIndexService.upsert_item(db, int(item.id))
                success_count += 1
            except Exception as err:
                print(f"[rebuild-search-index] failed item_id={item.id} error={err}")

        print(f"[rebuild-search-index] success={success_count}")
        return success_count
    finally:
        db.close()


if __name__ == "__main__":
    run()
