"""
对话相关 API
"""
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db
from schemas import Response
from schemas.chat import (
    ChatRequest, ChatResponse, ChatHistoryResponse,
    ChatMessageResponse, SummarizeRequest, SummarizeResponse,
    VoiceTTSRequest, VoiceTTSResponse
)
from services import ChatService
from services.item_service import ItemService
from services.llm_service import summarize_chat

router = APIRouter(prefix="/chat", tags=["对话找物"])


def get_current_user(user_id: Optional[str] = Header(None, alias="X-User-Id")) -> str:
    """获取当前用户ID"""
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")
    return user_id


@router.post("", response_model=Response[ChatResponse])
async def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """对话找物（意图由 DeepSeek 解析，失败时回退规则）"""
    result = await ChatService.chat(
        db=db,
        family_id=request.family_id,
        user_id=user_id,
        message=request.message,
        session_id=request.session_id
    )
    return Response(data=ChatResponse(**result))


@router.get("/history", response_model=Response[ChatHistoryResponse])
async def get_chat_history(
    family_id: str,
    session_id: str,
    limit: int = 50,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取对话历史"""
    messages = ChatService.get_history(db, family_id, session_id, limit)

    result = []
    for m in messages:
        matched_items = None
        if m.matched_items:
            try:
                ids = json.loads(m.matched_items)
                if ids:
                    items = ItemService.get_by_ids(db, ids)
                    matched_items = ChatService._items_to_dict(items)
            except (json.JSONDecodeError, TypeError):
                pass
        result.append(ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            intent=m.intent,
            created_at=m.created_at,
            matched_items=matched_items
        ))

    return Response(data=ChatHistoryResponse(
        session_id=session_id,
        messages=result
    ))


@router.post("/summarize", response_model=Response[SummarizeResponse])
async def summarize_chat_history(
    request: SummarizeRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """聊天记录压缩总结：拉取当前会话历史，调用 DeepSeek 生成一段总结"""
    messages = ChatService.get_history(
        db, request.family_id, request.session_id, limit=100
    )
    if not messages:
        return Response(data=SummarizeResponse(summary="暂无对话记录可总结。"))

    llm_messages = [
        {"role": m.role, "content": m.content or ""}
        for m in messages
    ]
    try:
        summary = await summarize_chat(llm_messages)
        return Response(data=SummarizeResponse(summary=summary))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"DeepSeek 请求失败: {e.response.status_code}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"总结失败: {str(e)}")


@router.delete("/history", response_model=Response)
async def clear_chat_history(
    family_id: str,
    session_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空对话历史"""
    success = ChatService.clear_history(db, family_id, session_id)
    
    if not success:
        return Response(message="无对话历史")
    
    return Response(message="对话历史已清空")


@router.post("/voice/recognize", response_model=Response[dict])
async def voice_recognize(
    file: UploadFile = File(..., description="录音文件，表单字段名须为 file"),
    scene: str = Form("common"),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """语音识别（百炼 Fun-ASR），需配置 BAILIAN_API_KEY 与 BACKEND_PUBLIC_URL"""
    import logging
    from config.settings import settings
    import uuid

    logger = logging.getLogger(__name__)
    print(
        "[voice/recognize] 收到请求",
        f"filename={getattr(file, 'filename', None)}",
        f"content_type={getattr(file, 'content_type', None)}",
    )
    audio_data = await file.read()
    print("[voice/recognize] body_size=", len(audio_data))
    if not audio_data:
        raise HTTPException(status_code=400, detail="音频为空")
    if not (settings.BAILIAN_API_KEY and settings.BACKEND_PUBLIC_URL):
        return Response(data={"text": "", "duration": 0, "entities": None})

    file_id = uuid.uuid4().hex
    voice_temp_dir = settings.UPLOAD_DIR / "voice_temp"
    voice_temp_dir.mkdir(parents=True, exist_ok=True)
    path = None
    ext = ".mp3"
    final_filename = f"{file_id}{ext}"

    try:
        from services.voice_audio_service import detect_voice_extension, prepare_voice_file

        ext = detect_voice_extension(file.filename, audio_data)
        path, final_filename, transform_desc = prepare_voice_file(audio_data, ext, voice_temp_dir, file_id)
        if final_filename.endswith(".wav"):
            print(f"[voice/recognize] 已处理为 wav source_ext={ext} transform={transform_desc} size={path.stat().st_size}")
        else:
            logger.warning(
                "voice/recognize: 未转 wav，使用原格式 %s，文件头 hex=%s",
                ext,
                audio_data[:32].hex() if len(audio_data) >= 32 else audio_data.hex(),
            )
            print(
                "[voice/recognize] 未转 wav",
                f"ext={ext}",
                f"transform={transform_desc}",
                f"head_hex={audio_data[:32].hex() if len(audio_data) >= 32 else audio_data.hex()}",
            )
    except Exception as e:
        logger.warning(
            "voice/recognize: 预处理失败 error=%s，文件头 hex=%s",
            e,
            audio_data[:32].hex() if len(audio_data) >= 32 else audio_data.hex(),
        )
        print(
            "[voice/recognize] 预处理失败",
            f"error={e}",
            f"head_hex={audio_data[:32].hex() if len(audio_data) >= 32 else audio_data.hex()}",
        )
        path = voice_temp_dir / f"{file_id}{ext}"
        path.write_bytes(audio_data)
        final_filename = path.name

    public_url = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/uploads/voice_temp/{final_filename}"
    logger.warning(
        "voice/recognize: filename=%s ext=%s size=%s public_url=%s",
        file.filename,
        ext,
        len(audio_data),
        public_url,
    )
    print(
        "[voice/recognize] 保存完成",
        f"ext={ext}",
        f"final_filename={final_filename}",
        f"public_url={public_url}",
    )

    import asyncio
    try:
        from services.bailian_asr_service import recognize as bailian_recognize
        from services.llm_service import parse_store_voice_entities
        # 为了调试方便，暂时不删除临时语音文件，方便通过 URL 手动访问和排查格式问题
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            bailian_recognize,
            final_filename,
            settings.BACKEND_PUBLIC_URL.rstrip("/"),
        )
        text = ((result or {}).get("text") or "").strip()
        if scene == "store" and text:
            try:
                result["entities"] = await parse_store_voice_entities(text)
            except Exception as e:
                logger.warning("store 语音实体抽取失败: %s", e)
        return Response(data=result)
    except ValueError as e:
        msg = str(e)
        if "ASR_RESPONSE_HAVE_NO_WORDS" in msg:
            return Response(
                message="无法识别出文字",
                data={"text": "", "duration": 0, "entities": None},
            )
        if "DECODE_ERROR" in msg or "解码" in msg:
            msg = "音频格式无法识别。建议：1）本机安装 ffmpeg 后重启后端再试；2）或用真机预览录音（模拟器格式与真机不同）"
        raise HTTPException(status_code=400, detail=msg)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"百炼 ASR 请求失败: {e.response.status_code}")


@router.post("/voice/tts", response_model=Response[VoiceTTSResponse])
async def text_to_speech(
    request: VoiceTTSRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """文字转语音（百炼 TTS），未配置时返回占位"""
    from config.settings import settings
    from services.tts_service import synthesize as tts_synthesize

    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本为空")
    if not settings.BAILIAN_API_KEY:
        return Response(data=VoiceTTSResponse(
            audio_url="",
            duration=0,
        ))
    try:
        speed = 0.5 + request.speed / 10.0  # 1~10 -> 0.55~1.5
        out = tts_synthesize(text, voice="Cherry", speed=speed)
        return Response(data=VoiceTTSResponse(
            audio_url=out["audio_url"],
            duration=out["duration"],
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"TTS 请求失败: {e.response.status_code}")