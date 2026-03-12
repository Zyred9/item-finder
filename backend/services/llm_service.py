"""
LLM 调用服务：优先百炼 Coding Plan（OpenAI 兼容），未配置时用 DeepSeek。
用于：对话总结、找物意图解析。
"""
import json
import httpx
from typing import List, Dict, Any, Tuple, Optional

from config.settings import settings, get_deepseek_api_key, get_coding_plan_api_key


DEEPSEEK_MODEL = "deepseek-chat"
SUMMARY_SYSTEM = """你是一个「寻物记」小程序的助手。用户会发来一段找物对话的完整记录（多轮用户提问与助手回复）。
请用简洁的中文，把这段对话压缩总结成一段话，方便用户快速回顾。要求：
1. 只输出总结内容，不要加「总结：」等前缀。
2. 突出「问过什么」「找到了哪些物品/位置」。
3. 控制在 200 字以内。"""

INTENT_SYSTEM = """你是「寻物记」小程序的意图解析器。用户会发一句话，你需要判断意图并抽取关键信息。
只输出一个 JSON 对象，不要其他内容。格式严格如下：
{"intent": "search" | "query_expire" | "unknown", "keyword": "字符串或空"}

规则：
- intent 为 search：用户在找东西、问某物在哪、问位置。keyword 填要查找的物品名或关键词（如「护照」「感冒药」「吹风机」），去掉「在哪」「在哪里」「放哪了」等词后剩下的核心词；若整句与找物无关则 keyword 为空。
- intent 为 query_expire：用户问过期、保质期、快过期了等。
- intent 为 unknown：无法判断或与找物/过期无关。keyword 为空。

示例：
用户：「我的护照在哪」 -> {"intent": "search", "keyword": "护照"}
用户：「吹风机放哪了」 -> {"intent": "search", "keyword": "吹风机"}
用户：「有什么快过期了」 -> {"intent": "query_expire", "keyword": ""}
用户：「你好」 -> {"intent": "unknown", "keyword": ""}"""

STORE_VOICE_SYSTEM = """你是「寻物记」小程序的存物语音抽取器。
用户会说一句和“存放物品”相关的话，请从中提取结构化字段（含过期/保修等时间）。
只输出一个 JSON 对象，不要其他内容。格式严格如下：
{"item_name": "字符串或空", "location": "字符串或空", "category_name": "字符串或空", "description": "字符串或空",
 "expire_date": "YYYY-MM-DD或空", "production_date": "YYYY-MM-DD或空", "shelf_life_days": 数字或空,
 "open_date": "YYYY-MM-DD或空", "open_shelf_life": 数字或空, "warranty_date": "YYYY-MM-DD或空"}

规则：
- item_name：物品名称；location：存放位置；category_name：分类中文名；description：简短说明
- expire_date：过期日期，如“保质期到12月31日”“过期时间2026年3月” → 转为 YYYY-MM-DD，无法推断则空字符串
- production_date：生产日期；shelf_life_days：保质期天数（整数）
- open_date：开封日期；open_shelf_life：开封后保质期天数（整数）
- warranty_date：保修到期日，如“保修到明年6月” → YYYY-MM-DD
- 日期统一用 YYYY-MM-DD，没有则空字符串；天数为整数，没有则 null 或省略
- 只返回 JSON，不要 markdown，不要解释
"""


def _get_chat_client() -> Tuple[str, str, str]:
    """
    优先使用百炼 Coding Plan，否则 DeepSeek。
    API Key 均从环境变量名读取（CODING_PLAN_ENV_KEY_NAME / DEEPSEEK_ENV_KEY_NAME）。
    :return: (base_url, api_key, model)，base_url 为根地址（如 https://coding.dashscope.aliyuncs.com/v1）
    """
    key = get_coding_plan_api_key()
    base = (settings.CODING_PLAN_BASE_URL or "").strip().rstrip("/")
    if key and base:
        model = (settings.CODING_PLAN_MODEL or "qwen3.5-plus").strip() or "qwen3.5-plus"
        return (base, key, model)
    api_key = get_deepseek_api_key()
    if not api_key:
        raise ValueError(
            "未配置 LLM：请在环境变量中设置 CODING_PLAN 的 Key（配置项 CODING_PLAN_ENV_KEY_NAME 对应变量），"
            f"或设置 DeepSeek 的 Key（配置项 {settings.DEEPSEEK_ENV_KEY_NAME} 对应变量）"
        )
    base = settings.DEEPSEEK_BASE_URL.rstrip("/")
    return (base, api_key, DEEPSEEK_MODEL)


def _chat_completions_url(base_url: str) -> str:
    """返回完整的 chat/completions URL（OpenAI 兼容）。"""
    b = base_url.rstrip("/")
    if b.endswith("/v1"):
        return f"{b}/chat/completions"
    if b.endswith("/v1/"):
        return f"{b.rstrip('/')}/chat/completions"
    return f"{b}/v1/chat/completions"


async def parse_store_voice_entities(user_message: str) -> Dict[str, str]:
    """
    使用 DeepSeek 从存物语音文本中提取物品名、位置、分类名。
    这里按用户要求固定走 DeepSeek，不走 Coding Plan。
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        raise ValueError(
            f"未配置 DeepSeek Key（请设置环境变量 {settings.DEEPSEEK_ENV_KEY_NAME}）"
        )

    message = (user_message or "").strip()
    if not message:
        return {
            "item_name": "",
            "location": "",
            "category_name": "",
            "description": "",
        }

    url = _chat_completions_url(settings.DEEPSEEK_BASE_URL.rstrip("/"))
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body: Dict[str, Any] = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": STORE_VOICE_SYSTEM},
            {"role": "user", "content": message},
        ],
        "max_tokens": 256,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    choice = (data.get("choices") or [None])[0]
    if not choice:
        raise ValueError("LLM 返回无 choices")

    content = (choice.get("message") or {}).get("content") or "{}"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("LLM 返回非 JSON")

    def _date(s: Any) -> str:
        if s is None or s == "":
            return ""
        s = str(s).strip()
        if not s or s.lower() in ("null", "none"):
            return ""
        return s

    def _int(s: Any) -> Optional[int]:
        if s is None or s == "":
            return None
        try:
            return int(s)
        except (TypeError, ValueError):
            return None

    out = {
        "item_name": (parsed.get("item_name") or "").strip(),
        "location": (parsed.get("location") or "").strip(),
        "category_name": (parsed.get("category_name") or "").strip(),
        "description": (parsed.get("description") or "").strip(),
        "expire_date": _date(parsed.get("expire_date")),
        "production_date": _date(parsed.get("production_date")),
        "shelf_life_days": _int(parsed.get("shelf_life_days")),
        "open_date": _date(parsed.get("open_date")),
        "open_shelf_life": _int(parsed.get("open_shelf_life")),
        "warranty_date": _date(parsed.get("warranty_date")),
    }
    # 日志：存物语音实体抽取结果
    try:
        print("[llm] store_voice_entities:", json.dumps(out, ensure_ascii=False))
    except Exception:
        print("[llm] store_voice_entities (raw):", out)
    return out


EXTRACT_EXTENSION_SYSTEM = """你从一段文字（可能来自说明书、药盒、发票、证件等）中提取与「保质/过期/保修」相关的日期与数字。
只输出一个 JSON 对象，不要其他内容。格式严格如下：
{"expire_date": "YYYY-MM-DD或空", "production_date": "YYYY-MM-DD或空", "shelf_life_days": 数字或null,
 "open_date": "YYYY-MM-DD或空", "open_shelf_life": 数字或null, "warranty_date": "YYYY-MM-DD或空"}

规则：
- expire_date：过期日期、保质期至、有效期至、Use by 等；production_date：生产日期、生产批号对应日期
- shelf_life_days：保质期天数（如 365、24个月按 730）；没有则 null
- open_date：开封日期；open_shelf_life：开封后保质期天数（如开封后28天）
- warranty_date：保修至、保修期至、保修到期
- 日期统一 YYYY-MM-DD，无法推断则空字符串；只返回 JSON
"""


async def extract_extension_from_text(text: str) -> Dict[str, Any]:
    """
    从 OCR 等文本中抽取过期/生产/保修相关字段，供存物扩展信息自动填充。
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        return {}
    message = (text or "").strip()[:3000]
    if not message:
        return {}

    url = _chat_completions_url(settings.DEEPSEEK_BASE_URL.rstrip("/"))
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body: Dict[str, Any] = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACT_EXTENSION_SYSTEM},
            {"role": "user", "content": message},
        ],
        "max_tokens": 256,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return {}

    choice = (data.get("choices") or [None])[0]
    if not choice:
        return {}
    content = (choice.get("message") or {}).get("content") or "{}"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {}

    def _d(s: Any) -> str:
        if s is None or s == "":
            return ""
        s = str(s).strip()
        return s if s and s.lower() not in ("null", "none") else ""

    def _n(s: Any) -> Optional[int]:
        if s is None or s == "":
            return None
        try:
            return int(s)
        except (TypeError, ValueError):
            return None

    out: Dict[str, Any] = {}
    if _d(parsed.get("expire_date")):
        out["expire_date"] = _d(parsed.get("expire_date"))
    if _d(parsed.get("production_date")):
        out["production_date"] = _d(parsed.get("production_date"))
    if _n(parsed.get("shelf_life_days")) is not None:
        out["shelf_life_days"] = _n(parsed.get("shelf_life_days"))
    if _d(parsed.get("open_date")):
        out["open_date"] = _d(parsed.get("open_date"))
    if _n(parsed.get("open_shelf_life")) is not None:
        out["open_shelf_life"] = _n(parsed.get("open_shelf_life"))
    if _d(parsed.get("warranty_date")):
        out["warranty_date"] = _d(parsed.get("warranty_date"))
    # 日志：OCR 文本扩展字段抽取结果
    try:
        print("[llm] extract_extension_from_text:", json.dumps(out, ensure_ascii=False))
    except Exception:
        print("[llm] extract_extension_from_text (raw):", out)
    return out


async def summarize_chat(messages: List[Dict[str, str]]) -> str:
    """
    将多轮对话压缩成一段总结。优先 Coding Plan，否则 DeepSeek。
    """
    try:
        base, api_key, model = _get_chat_client()
    except ValueError as e:
        raise e

    payload_messages: List[Dict[str, str]] = [{"role": "system", "content": SUMMARY_SYSTEM}]
    for m in messages:
        role = m.get("role") or "user"
        content = (m.get("content") or "").strip()
        if content:
            payload_messages.append({"role": role, "content": content})

    if len(payload_messages) <= 1:
        return "暂无有效对话内容可总结。"

    url = _chat_completions_url(base)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body: Dict[str, Any] = {
        "model": model,
        "messages": payload_messages,
        "max_tokens": 512,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    choice = (data.get("choices") or [None])[0]
    if not choice:
        raise ValueError("LLM 返回无 choices")
    content = (choice.get("message") or {}).get("content") or ""
    return content.strip() or "未能生成总结。"


async def parse_find_intent(user_message: str) -> Dict[str, str]:
    """
    解析用户一句话的意图与关键词，用于对话找物。优先 Coding Plan，否则 DeepSeek。
    """
    try:
        base, api_key, model = _get_chat_client()
    except ValueError as e:
        raise e

    message = (user_message or "").strip()
    if not message:
        return {"intent": "unknown", "keyword": ""}

    url = _chat_completions_url(base)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": message},
        ],
        "max_tokens": 128,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    choice = (data.get("choices") or [None])[0]
    if not choice:
        raise ValueError("LLM 返回无 choices")
    content = (choice.get("message") or {}).get("content") or "{}"

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("LLM 返回非 JSON")

    intent = (parsed.get("intent") or "unknown").strip().lower()
    if intent not in ("search", "query_expire", "unknown"):
        intent = "unknown"
    keyword = (parsed.get("keyword") or "").strip()

    return {"intent": intent, "keyword": keyword}
