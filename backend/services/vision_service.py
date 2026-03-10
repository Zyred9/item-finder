"""
百炼 · 存物主图理解（Qwen-VL）
拍照识物，建议名称与分类。
"""
import base64
import json
import re

import httpx

from config.settings import settings

# 百炼 OpenAI 兼容接口（多模态）
BAILIAN_VL_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL_VL = "qwen3-vl-plus"  # 存物主图理解
PROMPT = """这是一张用户要存放的物品照片。请用一句话描述这是什么物品，并给出一个简短的中文分类建议（如：电子产品、日用品、证件、药品、服饰、食品等）。
只返回一行 JSON，不要其他说明，格式严格为：{"name":"物品名称","category_suggestion":"分类建议"}"""


def _get_api_key() -> str:
    key = (settings.BAILIAN_API_KEY or "").strip()
    if not key:
        raise ValueError("未配置 BAILIAN_API_KEY（百炼存物主图理解需在 .env 中配置）")
    return key


def understand_item_photo(image_data: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    根据主图理解物品，返回建议名称和分类。
    :param image_data: 图片二进制
    :param mime_type: image/jpeg 或 image/png
    :return: {"suggested_name": str, "suggested_category": str}
    """
    api_key = _get_api_key()
    b64 = base64.b64encode(image_data).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    payload = {
        "model": MODEL_VL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "max_tokens": 256,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(BAILIAN_VL_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    choices = data.get("choices") or []
    if not choices:
        return {"suggested_name": "", "suggested_category": ""}
    content = (choices[0].get("message") or {}).get("content") or ""
    content = content.strip()

    # 尝试解析 JSON（可能被 markdown 包裹）
    name, category = "", ""
    try:
        m = re.search(r"\{[^{}]+\}", content)
        if m:
            obj = json.loads(m.group())
            name = (obj.get("name") or "").strip()
            category = (obj.get("category_suggestion") or "").strip()
    except (json.JSONDecodeError, TypeError):
        pass
    if not name and content:
        name = content[:50]
    return {"suggested_name": name, "suggested_category": category}
