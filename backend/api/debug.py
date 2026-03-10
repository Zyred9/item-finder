import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body


router = APIRouter(tags=["Debug"])


def _append_ndjson(payload: Dict[str, Any]) -> None:
    log_path = Path(__file__).resolve().parents[3] / "debug-fbaaed.log"
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


@router.post("/debug/log")
async def debug_log(
    payload: Dict[str, Any] = Body(...),
    session_id: Optional[str] = None,
    run_id: Optional[str] = None,
    hypothesis_id: Optional[str] = None,
    location: Optional[str] = None,
    message: Optional[str] = None,
    timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """
    真机调试埋点落盘（NDJSON）。仅用于本地调试，不要在生产环境开放。
    """
    safe_payload: Dict[str, Any] = {
        "sessionId": payload.get("sessionId") or session_id,
        "runId": payload.get("runId") or run_id,
        "hypothesisId": payload.get("hypothesisId") or hypothesis_id,
        "location": payload.get("location") or location,
        "message": payload.get("message") or message,
        "timestamp": payload.get("timestamp") or timestamp,
        "data": payload.get("data") if isinstance(payload.get("data"), dict) else {},
    }

    # 控制体积，避免意外写入大字段
    if len(json.dumps(safe_payload.get("data", {}), ensure_ascii=False)) > 8_000:
        safe_payload["data"] = {"_truncated": True}

    _append_ndjson(safe_payload)
    return {"ok": True}

