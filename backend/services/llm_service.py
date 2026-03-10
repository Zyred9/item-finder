"""
LLM 调用服务：优先百炼 Coding Plan（OpenAI 兼容），未配置时用 DeepSeek。
用于：对话总结、找物意图解析。
"""
import json
import httpx
from typing import List, Dict, Any, Tuple

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
用户会说一句和“存放物品”相关的话，请从中提取结构化字段。
只输出一个 JSON 对象，不要其他内容。格式严格如下：
{"item_name": "字符串或空", "location": "字符串或空", "category_name": "字符串或空", "description": "字符串或空"}

规则：
- item_name：物品名称，如“护照”“吹风机”“退烧药”
- location：存放位置，如“书房第二层抽屉”“客厅电视柜下面”
- category_name：分类中文名称，如“证件”“电器”“药品”；无法判断则为空
- description：保留一句简短说明；若没有额外说明，可直接复用用户原句或概括
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

    return {
        "item_name": (parsed.get("item_name") or "").strip(),
        "location": (parsed.get("location") or "").strip(),
        "category_name": (parsed.get("category_name") or "").strip(),
        "description": (parsed.get("description") or "").strip(),
    }


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
