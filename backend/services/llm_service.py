"""
LLM 服务（意图识别、语音识别、总结等）
"""
import json
import re
from typing import Any, Dict, List, Tuple
import httpx
from datetime import datetime

from config.settings import settings
from config.constants import DEEPSEEK_MODEL, CODING_PLAN_MODEL


def get_deepseek_api_key() -> str:
    """获取 DeepSeek API Key"""
    return (getattr(settings, settings.DEEPSEEK_ENV_KEY_NAME, "") or "").strip()


def get_coding_plan_api_key() -> str:
    """获取 Coding Plan API Key"""
    return (getattr(settings, settings.CODING_PLAN_ENV_KEY_NAME, "") or "").strip()


def _date(v: Any) -> Any:
    if not v:
        return None
    s = str(v).strip()
    if not s:
        return None
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _int(v: Any) -> Any:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


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
    return f"{b}/v1/chat/completions"


INTENT_SYSTEM = """你是「寻物记」小程序的意图识别助手。
用户会发一句话，你需要判断意图并提取关键词。
只输出一个 JSON 对象，不要其他内容。格式严格如下：
{"intent": "search" | "query_expire" | "unknown", "keyword": "字符串或空"}

规则：
- intent 为 search（搜索类）：
  1. 用户要找某个物品，或问位置。keyword 为要找的物品关键词，如「护照」「感冒药」「鱼饲料」等
  2. 用户问某个位置里有什么，如「客厅里有什么」「药箱里有啥」「主卧抽屉有什么」等。此时 keyword 为位置关键词，如「客厅」「药箱」「主卧抽屉」等
- intent 为 query_expire：用户问过期、保质期等相关内容
- intent 为 unknown：无法判断或与物品/位置无关。keyword 为空

示例：
用户说：「我的护照在哪」 -> {"intent": "search", "keyword": "护照"}
用户说：「感冒药放哪里了」 -> {"intent": "search", "keyword": "感冒药"}
用户说：「客厅里有什么」 -> {"intent": "search", "keyword": "客厅"}
用户说：「药箱里有啥」 -> {"intent": "search", "keyword": "药箱"}
用户说：「有什么东西快过期了」 -> {"intent": "query_expire", "keyword": ""}
用户说：「你好」 -> {"intent": "unknown", "keyword": ""}
"""


async def parse_find_intent(message: str) -> Dict[str, Any]:
    """
    解析用户输入，识别找物意图。
    :return: {"intent": "search"|"query_expire"|"unknown", "keyword": "..."}
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        return {"intent": "unknown", "keyword": ""}
    
    message = (message or "").strip()
    if not message:
        return {"intent": "unknown", "keyword": ""}
    
    url = _chat_completions_url(settings.DEEPSEEK_BASE_URL.rstrip("/"))
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body: Dict[str, Any] = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": message},
        ],
        "max_tokens": 128,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[llm][parse_find_intent] error: {e}")
        return {"intent": "unknown", "keyword": ""}
    
    choices = data.get("choices") or []
    if not choices:
        return {"intent": "unknown", "keyword": ""}
    
    content = (choices[0].get("message") or {}).get("content") or ""
    content = content.strip()
    
    # 尝试提取 JSON
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return {"intent": "unknown", "keyword": ""}
    
    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        return {"intent": "unknown", "keyword": ""}
    
    intent = (parsed.get("intent") or "unknown").strip().lower()
    keyword = (parsed.get("keyword") or "").strip()
    
    if intent not in ("search", "query_expire", "unknown"):
        intent = "unknown"
        keyword = ""
    
    return {"intent": intent, "keyword": keyword}


STORE_VOICE_SYSTEM = """你是「寻物记」小程序的存物语音抽取器。
用户会说一句和"存放物品"相关的话，请从中提取结构化字段（含过期/保修等时间）。
只输出一个 JSON 对象，不要其他内容。格式严格如下：
{"item_name": "字符串或空", "location": "字符串或空", "category_name": "字符串或空", "description": "字符串或空",
 "expire_date": "YYYY-MM-DD 或空", "production_date": "YYYY-MM-DD 或空", "shelf_life_days": 数字或空，
 "warranty_date": "YYYY-MM-DD 或空"}

规则：
- item_name：物品名称；location：存放位置；category_name：分类中文名；description：简短说明
- expire_date：过期日期，如"保质期到 12 月 31 日""过期时间 2026 年 3 月" → 转为 YYYY-MM-DD，无法推断则空字符串
- production_date：生产日期；shelf_life_days：保质期天数（整数）
- warranty_date：保修到期日，如"保修到明年 6 月" → YYYY-MM-DD
- 日期统一用 YYYY-MM-DD，没有则空字符串；天数为整数，没有则 null 或省略
- 只返回 JSON，不要 markdown，不要解释
"""


async def parse_store_voice_entities(audio_file_path: str) -> Dict[str, Any]:
    """
    上传音频到 DeepSeek，解析存物相关实体。
    :return: {"item_name": "...", "location": "...", "category_name": "...", "description": "...",
              "expire_date": "...", "production_date": "...", "shelf_life_days": 180, "warranty_date": "..."}
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        return {}
    
    url = _chat_completions_url(settings.DEEPSEEK_BASE_URL.rstrip("/"))
    headers = {"Authorization": f"Bearer {api_key}"}
    
    with open(audio_file_path, "rb") as f:
        files = {"file": f}
        data = {"model": DEEPSEEK_MODEL, "prompt": STORE_VOICE_SYSTEM}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, files=files, data=data)
                resp.raise_for_status()
                result = resp.json()
        except Exception as e:
            print(f"[llm][parse_store_voice_entities] error: {e}")
            return {}
    
    text = (result.get("choices") or [{}])[0].get("text") or ""
    text = text.strip()
    
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    
    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        return {}
    
    def _d(v):
        return _date(v)
    
    def _n(v):
        return _int(v)
    
    out = {
        "item_name": (parsed.get("item_name") or "").strip(),
        "location": (parsed.get("location") or "").strip(),
        "category_name": (parsed.get("category_name") or "").strip(),
        "description": (parsed.get("description") or "").strip(),
        "expire_date": _d(parsed.get("expire_date")),
        "production_date": _d(parsed.get("production_date")),
        "shelf_life_days": _n(parsed.get("shelf_life_days")),
        "warranty_date": _d(parsed.get("warranty_date")),
    }
    
    return {k: v for k, v in out.items() if v is not None and v != ""}


EXTRACT_EXTENSION_SYSTEM = """你从一段文字（可能来自说明书、药盒、发票、证件等）中提取与「保质/过期/保修」相关的日期与数字。
只输出一个 JSON 对象，不要其他内容。格式严格如下：
{"expire_date": "YYYY-MM-DD 或空", "production_date": "YYYY-MM-DD 或空", "shelf_life_days": 数字或 null,
 "warranty_date": "YYYY-MM-DD 或空"}

规则：
- expire_date：过期日期、保质期至、有效期至、Use by 等；production_date：生产日期、生产批号对应日期
- shelf_life_days：保质期天数（如 365、24 个月按 730）；没有则 null
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
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[llm][extract_extension_from_text] error: {e}")
        return {}
    
    choices = data.get("choices") or []
    if not choices:
        return {}
    
    content = (choices[0].get("message") or {}).get("content") or ""
    content = content.strip()
    
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return {}
    
    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        return {}
    
    def _d(v):
        return _date(v)
    
    def _n(v):
        return _int(v)
    
    out: Dict[str, Any] = {}
    if _d(parsed.get("expire_date")):
        out["expire_date"] = _d(parsed.get("expire_date"))
    if _d(parsed.get("production_date")):
        out["production_date"] = _d(parsed.get("production_date"))
    if _n(parsed.get("shelf_life_days")) is not None:
        out["shelf_life_days"] = _n(parsed.get("shelf_life_days"))
    if _d(parsed.get("warranty_date")):
        out["warranty_date"] = _d(parsed.get("warranty_date"))
    
    return out


SUMMARY_SYSTEM = """你是「寻物记」小程序的对话总结助手。
请将多轮对话总结成一段简洁的文字，概括用户找了哪些物品，分别在哪里。
只输出总结文字，不要 JSON，不要其他内容。
"""


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
    body = {
        "model": model,
        "messages": payload_messages,
        "max_tokens": 512,
        "temperature": 0.3,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[llm][summarize_chat] error: {e}")
        return "总结失败，请稍后重试。"
    
    choices = data.get("choices") or []
    if not choices:
        return "总结失败，请稍后重试。"
    
    content = (choices[0].get("message") or {}).get("content") or ""
    return content.strip()
