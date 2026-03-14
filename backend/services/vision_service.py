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
_PROMPT_TEMPLATE = """这是一张用户要存放的物品照片。请识别并返回以下信息（仅当图中可见时填写，不可见则对应字段为空字符串）：
1. 物品名称
2. 从下列分类中选一个最匹配的（必须原文返回，若都不匹配则填"其他"）：
{category_list}
3. 与保质/过期/保修相关的日期：过期日期、生产日期、保修到期日（若图中有）

只返回一行 JSON，不要其他说明，格式严格为：
{{"name":"物品名称","category_suggestion":"分类名称（原文）",
 "expire_date":"YYYY-MM-DD或空","production_date":"YYYY-MM-DD或空","warranty_date":"YYYY-MM-DD或空"}}

日期必须从图中文字识别（如保质期至、生产日期、有效期至、保修至等）。图中常见格式如 2025.08.28、2027.02.27 请转为 YYYY-MM-DD 返回；无法识别则空字符串。"""

# 不传分类时用的兜底提示词
_PROMPT_NO_CATS = """这是一张用户要存放的物品照片。请识别并返回以下信息（仅当图中可见时填写，不可见则对应字段为空字符串）：
1. 物品名称与分类建议
2. 与保质/过期/保修相关的日期：过期日期、生产日期、保修到期日（若图中有）

只返回一行 JSON，不要其他说明，格式严格为：
{"name":"物品名称","category_suggestion":"分类建议",
 "expire_date":"YYYY-MM-DD或空","production_date":"YYYY-MM-DD或空","warranty_date":"YYYY-MM-DD或空"}

日期必须从图中文字识别（如保质期至、生产日期、有效期至、保修至等）。图中常见格式如 2025.08.28、2027.02.27 请转为 YYYY-MM-DD 返回；无法识别则空字符串。"""


def _normalize_date(s: str) -> str:
    """将 2025.08.28 / 2025-08-28 / 2025/08/28 等统一为 YYYY-MM-DD。"""
    if not s or not isinstance(s, str):
        return ""
    s = s.strip().replace(" ", "")
    # 点、斜杠统一为 -
    for sep in (".", "/", "．"):
        s = s.replace(sep, "-")
    # 匹配 YYYY-MM-DD 或 YYYYMMDD
    m = re.match(r"(\d{4})[-]?(\d{1,2})[-]?(\d{1,2})", s)
    if m:
        y, mo, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
        return f"{y}-{mo}-{d}"
    return s if re.match(r"\d{4}-\d{2}-\d{2}", s) else ""


def _get_api_key() -> str:
    key = (settings.BAILIAN_API_KEY or "").strip()
    if not key:
        raise ValueError("未配置 BAILIAN_API_KEY（百炼存物主图理解需在 .env 中配置）")
    return key


def understand_item_photo(
    image_data: bytes,
    mime_type: str = "image/jpeg",
    available_categories: list | None = None,
) -> dict:
    """
    根据主图理解物品，返回建议名称和分类。
    :param image_data: 图片二进制
    :param mime_type: image/jpeg 或 image/png
    :return: {"suggested_name": str, "suggested_category": str}
    """
    api_key = _get_api_key()
    b64 = base64.b64encode(image_data).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    if available_categories:
        cat_list = "\n".join(f"  - {c}" for c in available_categories)
        prompt = _PROMPT_TEMPLATE.format(category_list=cat_list)
    else:
        prompt = _PROMPT_NO_CATS

    payload = {
        "model": MODEL_VL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
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

    # 尝试解析 JSON（可能被 markdown 包裹）；支持嵌套花括号
    name, category = "", ""
    suggested_extension = {}
    try:
        m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content)
        if m:
            obj = json.loads(m.group())
            name = (obj.get("name") or "").strip()
            category = (obj.get("category_suggestion") or "").strip()
            for key in ("expire_date", "production_date", "warranty_date"):
                val = obj.get(key)
                if val and isinstance(val, str) and val.strip():
                    normalized = _normalize_date(val.strip())
                    if normalized:
                        suggested_extension[key] = normalized
    except (json.JSONDecodeError, TypeError):
        pass
    if not name and content:
        name = content[:50]
    result = {"suggested_name": name, "suggested_category": category}
    if suggested_extension:
        result["suggested_extension"] = suggested_extension
    # 日志：主图理解的原始解析结果，便于排查识别问题
    try:
        print("[vision] understand_item_photo result:", json.dumps(result, ensure_ascii=False))
    except Exception:
        print("[vision] understand_item_photo result (raw):", result)
    return result
