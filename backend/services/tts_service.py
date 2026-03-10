"""
百炼 · 文字转语音 TTS（qwen3-tts-flash）
用于找物结果播报等。
"""
import base64
import uuid
from pathlib import Path

import httpx

from config.settings import settings

# 百炼语音合成（多模态生成接口）
BAILIAN_TTS_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"


def synthesize(text: str, voice: str = "Cherry", speed: float = 1.0) -> dict:
    """
    调用百炼语音合成（qwen3-tts-flash），保存到本地并返回访问 URL。
    :param text: 待合成文本（最长 512 字符）
    :param voice: 音色，如 Cherry、Ethan、longxiaochun 等
    :param speed: 语速 0.5~2.0
    :return: {"audio_url": str, "duration": float}
    """
    api_key = (settings.BAILIAN_API_KEY or "").strip()
    if not api_key:
        raise ValueError("未配置 BAILIAN_API_KEY（百炼 TTS 需在 .env 中配置）")

    payload = {
        "model": "qwen3-tts-flash",
        "input": {
            "text": (text or "")[:512],
            "voice": voice,
            "language_type": "Chinese",
        },
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(BAILIAN_TTS_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    output = data.get("output") or {}
    audio_obj = output.get("audio") or {}
    audio_url_remote = audio_obj.get("url")
    audio_b64 = audio_obj.get("data")

    tts_dir = settings.UPLOAD_DIR / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.wav"
    local_path = tts_dir / filename

    if audio_url_remote:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(audio_url_remote)
            r.raise_for_status()
            local_path.write_bytes(r.content)
    elif audio_b64:
        local_path.write_bytes(base64.b64decode(audio_b64))
    else:
        raise ValueError("TTS 响应中无 output.audio.url 或 output.audio.data")

    duration = max(0.1, len(text) * 0.15)
    return {
        "audio_url": f"/uploads/tts/{filename}",
        "duration": duration,
    }
