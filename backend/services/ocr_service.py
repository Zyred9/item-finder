"""
百炼 · 扩展凭证 OCR（说明书、发票、药盒等）
使用通义 qwen-vl-ocr 模型。
"""
import base64

import httpx

from config.settings import settings

BAILIAN_OCR_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL_OCR = "qwen-vl-ocr"
PROMPT = "请提取图片中的全部文字，保持原有顺序和段落，直接输出文本，不要解释。"


def _get_api_key() -> str:
    key = (settings.BAILIAN_API_KEY or "").strip()
    if not key:
        raise ValueError("未配置 BAILIAN_API_KEY（百炼扩展凭证 OCR 需在 .env 中配置）")
    return key


def extract_text(image_data: bytes, mime_type: str = "image/jpeg") -> str:
    """
    对凭证/说明书/发票/药盒等图片做 OCR，返回提取的文本。
    :param image_data: 图片二进制
    :param mime_type: image/jpeg 或 image/png
    :return: 提取的文本
    """
    api_key = _get_api_key()
    b64 = base64.b64encode(image_data).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    payload = {
        "model": MODEL_OCR,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "max_tokens": 2048,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(BAILIAN_OCR_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    choices = data.get("choices") or []
    if not choices:
        return ""
    content = (choices[0].get("message") or {}).get("content") or ""
    return content.strip()
