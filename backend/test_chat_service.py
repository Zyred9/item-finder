import os
import sys
import unittest
from unittest.mock import AsyncMock, patch


sys.path.insert(0, os.path.dirname(__file__))


class _FakeDb:
    def __init__(self):
        self.records = []
        self.committed = False

    def add(self, record):
        self.records.append(record)

    def commit(self):
        self.committed = True


class _FakeItem:
    def __init__(self, item_id, name, location):
        self.id = item_id
        self.name = name
        self.location = location
        self.photo_path = ""
        self.created_at = None


class ChatServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_chat_should_fallback_to_rule_when_llm_returns_unknown_for_location_query(self):
        from services.chat_service import ChatService

        db = _FakeDb()
        fake_items = [_FakeItem(1, "护照", "主卧抽屉")]

        with patch(
            "services.chat_service.parse_find_intent",
            AsyncMock(return_value={"intent": "unknown", "keyword": ""}),
        ), patch(
            "services.chat_service.ItemService.search",
            return_value=fake_items,
        ):
            result = await ChatService.chat(
                db=db,
                family_id=1,
                user_id=1,
                message="主卧抽屉有什么",
                session_id="test-session",
            )

        self.assertEqual(result["intent"], "search")
        self.assertEqual(len(result["matched_items"]), 1)
        self.assertEqual(result["matched_items"][0]["name"], "护照")
        self.assertIn("主卧抽屉", result["reply"])
        self.assertTrue(db.committed)


if __name__ == "__main__":
    unittest.main()
