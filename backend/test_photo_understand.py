import os
import sys
import unittest
from unittest.mock import AsyncMock, patch


sys.path.insert(0, os.path.dirname(__file__))


class _FakeUploadFile:
    def __init__(self, filename: str = "demo.jpg", content: bytes = b"fake-image"):
        self.filename = filename
        self._content = content

    async def read(self):
        return self._content


class PhotoUnderstandTest(unittest.IsolatedAsyncioTestCase):
    async def test_photo_understand_falls_back_to_ocr_for_expire_date(self):
        from api.items import photo_understand
        from config.settings import settings

        fake_photo = _FakeUploadFile()

        with patch.object(settings, "BAILIAN_API_KEY", "test-key"), \
             patch("services.vision_service.understand_item_photo", return_value={
                 "suggested_name": "牛奶",
                 "suggested_category": "饮品",
             }), \
             patch("services.ocr_service.extract_text", return_value="保质期至 2027.02.27"), \
             patch(
                 "services.llm_service.extract_extension_from_text",
                 new=AsyncMock(return_value={"expire_date": "2027-02-27"}),
             ):
            response = await photo_understand(photo=fake_photo, user_id=1)

        self.assertEqual(response.data["suggested_name"], "牛奶")
        self.assertEqual(response.data["suggested_category"], "饮品")
        self.assertEqual(
            response.data.get("suggested_extension", {}).get("expire_date"),
            "2027-02-27",
        )


if __name__ == "__main__":
    unittest.main()
