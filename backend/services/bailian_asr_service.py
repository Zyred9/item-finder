"""
百炼 · Fun-ASR 录音文件识别
需公网可访问的音频 URL（BACKEND_PUBLIC_URL + /uploads/voice_temp/{filename}）。
"""
import logging
import time

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
TASKS_BASE = "https://dashscope.aliyuncs.com/api/v1/tasks"
MODEL = "fun-asr"
POLL_INTERVAL = 1.0
POLL_TIMEOUT = 120


def recognize(voice_temp_filename: str, public_base_url: str) -> dict:
    """
    使用百炼 Fun-ASR 识别录音文件。
    调用方需已将音频保存为 uploads/voice_temp/{voice_temp_filename}，
    voice_temp_filename 需带扩展名（如 xxx.mp3、xxx.m4a）。
    public_base_url 可被百炼服务访问（如 https://your-api.com）。
    :return: {"text": str, "duration": float, "entities": None}
    """
    api_key = (settings.BAILIAN_API_KEY or "").strip()
    if not api_key:
        raise ValueError("未配置 BAILIAN_API_KEY")
    base = (public_base_url or "").rstrip("/")
    if not base:
        raise ValueError("未配置 BACKEND_PUBLIC_URL（百炼 ASR 需公网可访问的音频 URL）")
    file_url = f"{base}/uploads/voice_temp/{voice_temp_filename}"
    logger.info("Fun-ASR 提交: file=%s url=%s", voice_temp_filename, file_url)
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(file_url)
            if r.status_code == 200:
                logger.info("公网 URL 可访问，百炼应能拉取音频")
            else:
                logger.warning("公网 URL 返回 %s，百炼可能无法拉取音频，请检查 cpolar 与 BACKEND_PUBLIC_URL", r.status_code)
    except Exception as e:
        logger.warning("公网 URL 自检失败（不影响识别）: %s", e)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": MODEL,
        "input": {"file_urls": [file_url]},
        "parameters": {"language_hints": ["zh", "en"]},
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(SUBMIT_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            err_body = resp.text
            logger.warning("Fun-ASR 提交失败 status=%s body=%s", resp.status_code, err_body)
            try:
                j = resp.json()
                raise ValueError(j.get("message") or j.get("detail") or err_body or "提交 ASR 任务失败")
            except ValueError:
                raise
            except Exception:
                raise ValueError(err_body or f"提交 ASR 任务失败: {resp.status_code}")
        data = resp.json()
    task_id = (data.get("output") or {}).get("task_id")
    if not task_id:
        msg = data.get("message") or data.get("detail") or "提交 ASR 任务失败"
        logger.warning("Fun-ASR 无 task_id: %s", data)
        raise ValueError(msg)

    start = time.monotonic()
    while time.monotonic() - start < POLL_TIMEOUT:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(f"{TASKS_BASE}/{task_id}", headers={"Authorization": f"Bearer {api_key}"})
            r.raise_for_status()
            out = r.json().get("output") or {}
        status = out.get("task_status")
        if status == "SUCCEEDED":
            return _parse_result(out)
        if status == "FAILED":
            msg = out.get("message") or out.get("error_message")
            if not msg and out.get("results"):
                first = out["results"][0] if isinstance(out["results"], list) else {}
                if isinstance(first, dict):
                    msg = first.get("message") or first.get("error_message") or msg
            msg = msg or "语音识别任务失败"
            logger.warning("Fun-ASR 任务失败: %s 完整 output=%s", msg, out)
            raise ValueError(msg)
        time.sleep(POLL_INTERVAL)

    raise ValueError("语音识别超时")


def _parse_result(output: dict) -> dict:
    results = output.get("results") or []
    if not results:
        return {"text": "", "duration": 0.0, "entities": None}
    first = results[0]
    if first.get("subtask_status") != "SUCCEEDED":
        return {"text": "", "duration": 0.0, "entities": None}
    transcription_url = first.get("transcription_url")
    if not transcription_url:
        return {"text": "", "duration": 0.0, "entities": None}
    with httpx.Client(timeout=15.0) as client:
        r = client.get(transcription_url)
        r.raise_for_status()
        body = r.json()
    transcripts = body.get("transcripts") or []
    parts = []
    duration_ms = 0
    for t in transcripts:
        if isinstance(t.get("text"), str):
            parts.append(t["text"].strip())
        duration_ms = max(duration_ms, t.get("content_duration_in_milliseconds") or 0)
    text = "".join(parts).strip() if parts else ""
    duration = duration_ms / 1000.0 if duration_ms else 0.0
    return {"text": text, "duration": duration, "entities": None}
