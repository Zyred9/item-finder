"""
语义搜索服务
"""
from typing import Dict, List, Tuple
import re

from models import Item
from config.settings import settings
from services.embedding_service import EmbeddingService
from services.search_index_service import SearchIndexService


class SemanticSearchService:
    """负责 query embedding、Qdrant 召回、MySQL 回表与排序"""

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", "", (text or "").strip().lower())

    @staticmethod
    def _build_query_terms(query_text: str) -> List[str]:
        normalized = SemanticSearchService._normalize_text(query_text)
        if not normalized:
            return []

        terms = {normalized}

        if len(normalized) >= 2:
            for idx in range(len(normalized) - 1):
                terms.add(normalized[idx: idx + 2])

        if len(normalized) >= 3:
            for idx in range(len(normalized) - 2):
                terms.add(normalized[idx: idx + 3])

        for char in normalized:
            terms.add(char)

        return sorted(terms, key=len, reverse=True)

    @staticmethod
    def _build_item_text(item: Item) -> str:
        parts = [
            getattr(item, "name", "") or "",
            getattr(item, "location", "") or "",
            getattr(item, "description", "") or "",
        ]
        return SemanticSearchService._normalize_text("".join(parts))

    @staticmethod
    def _lexical_match_ratio(query_text: str, item: Item) -> float:
        terms = SemanticSearchService._build_query_terms(query_text)
        if not terms:
            return 0.0
        item_text = SemanticSearchService._build_item_text(item)
        if not item_text:
            return 0.0

        matched_terms = [term for term in terms if term and term in item_text]
        if not matched_terms:
            return 0.0

        weighted_hit = sum(len(term) for term in matched_terms)
        weighted_all = sum(len(term) for term in terms)
        return weighted_hit / weighted_all if weighted_all else 0.0

    @staticmethod
    def _has_strong_keyword_overlap(query_text: str, item: Item, lexical_ratio: float) -> bool:
        item_text = SemanticSearchService._build_item_text(item)
        normalized_query = SemanticSearchService._normalize_text(query_text)
        if not item_text or not normalized_query:
            return False
        if normalized_query in item_text:
            return True

        terms = SemanticSearchService._build_query_terms(query_text)
        strong_terms = [term for term in terms if len(term) >= 2 and term in item_text]
        if strong_terms:
            return True

        if len(normalized_query) == 1:
            return normalized_query in item_text and lexical_ratio > 0

        return False

    @staticmethod
    def search_items(db, family_id: int, query_text: str, limit: int = 20) -> Tuple[List[Item], Dict[int, float]]:
        from services.item_service import ItemService

        keyword = (query_text or "").strip()
        if not keyword:
            return [], {}

        if not SearchIndexService.is_enabled():
            return ItemService.search_by_keyword(db, family_id, keyword, limit), {}

        try:
            query_vector = EmbeddingService.embed_text(keyword)
            points = SearchIndexService.search_points(
                query_vector=query_vector,
                family_id=family_id,
                limit=max(limit, settings.SEMANTIC_SEARCH_TOP_K),
            )
        except Exception as err:
            print(f"[semantic-search] semantic query failed, fallback to sql. error={err}")
            return ItemService.search_by_keyword(db, family_id, keyword, limit), {}

        if not points:
            return ItemService.search_by_keyword(db, family_id, keyword, limit), {}

        points = sorted(points, key=lambda point: float(point.get("score") or 0), reverse=True)
        score_map: Dict[int, float] = {}
        ordered_ids: List[int] = []
        for point in points:
            point_id = int(point["id"])
            score = float(point.get("score") or 0)
            if score < settings.SEMANTIC_SEARCH_MIN_SCORE:
                continue
            ordered_ids.append(point_id)
            score_map[point_id] = score

        if not ordered_ids:
            return ItemService.search_by_keyword(db, family_id, keyword, limit), {}

        mysql_items = ItemService.get_by_ids(db, ordered_ids)
        valid_items = [
            item for item in mysql_items
            if int(item.family_id) == int(family_id) and item.status == "active"
        ]
        item_map = {int(item.id): item for item in valid_items}

        reranked_items: List[tuple[float, Item]] = []
        for item_id in ordered_ids:
            item = item_map.get(int(item_id))
            if item:
                lexical_ratio = SemanticSearchService._lexical_match_ratio(keyword, item)
                if not SemanticSearchService._has_strong_keyword_overlap(keyword, item, lexical_ratio):
                    continue
                hybrid_score = score_map[item_id] + lexical_ratio
                setattr(item, "semantic_score", score_map[item_id])
                setattr(item, "lexical_match_ratio", lexical_ratio)
                reranked_items.append((hybrid_score, item))

        if not reranked_items:
            return ItemService.search_by_keyword(db, family_id, keyword, limit), {}

        reranked_items.sort(key=lambda pair: pair[0], reverse=True)
        ranked_items = [item for _, item in reranked_items[:limit]]
        return ranked_items, {int(item.id): score_map[int(item.id)] for item in ranked_items}
