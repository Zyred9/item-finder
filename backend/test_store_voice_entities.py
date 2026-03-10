import unittest
from unittest.mock import patch


class _FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"item_name":"护照","location":"书房第二层抽屉","category_name":"证件",'
                            '"description":"护照放在书房第二层抽屉"}'
                        )
                    }
                }
            ]
        }


class _FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def post(self, *args, **kwargs):
        return _FakeResponse()


class ParseStoreVoiceEntitiesTest(unittest.IsolatedAsyncioTestCase):
    async def test_parse_store_voice_entities_returns_structured_fields(self):
        from services import llm_service

        with patch("services.llm_service.get_deepseek_api_key", return_value="test-key"), \
             patch("services.llm_service.httpx.AsyncClient", _FakeClient):
            result = await llm_service.parse_store_voice_entities("把护照放在书房第二层抽屉")

        self.assertEqual(result["item_name"], "护照")
        self.assertEqual(result["location"], "书房第二层抽屉")
        self.assertEqual(result["category_name"], "证件")
        self.assertIn("护照", result["description"])


if __name__ == "__main__":
    unittest.main()
