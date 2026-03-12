"""
对话相关 Schema
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any


class ChatRequest(BaseModel):
    """对话请求"""
    family_id: int
    session_id: Optional[str] = None  # 不传则创建新会话
    message: str = Field(..., min_length=1, max_length=500)
    audio_path: Optional[str] = None  # 语音输入时使用


class ChatAction(BaseModel):
    """对话响应动作"""
    type: str  # navigate/photo/tts/detail
    label: str
    data: Optional[Any] = None


class ChatResponse(BaseModel):
    """对话响应"""
    reply: str
    session_id: str
    intent: Optional[str] = None
    matched_items: Optional[List[dict]] = None
    actions: Optional[List[ChatAction]] = None


class ChatMessageResponse(BaseModel):
    """对话消息响应"""
    id: int
    session_id: str
    role: str
    content: str
    intent: Optional[str]
    created_at: datetime
    matched_items: Optional[List[dict]] = None  # 历史中带搜索结果的条目

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    session_id: str
    messages: List[ChatMessageResponse]


class SummarizeRequest(BaseModel):
    """聊天记录压缩总结请求"""
    family_id: int
    session_id: str


class SummarizeResponse(BaseModel):
    """聊天记录压缩总结响应"""
    summary: str


class VoiceRecognizeResponse(BaseModel):
    """语音识别响应"""
    text: str
    duration: float
    entities: Optional[dict] = None


class VoiceTTSRequest(BaseModel):
    """文字转语音请求"""
    text: str = Field(..., max_length=500)
    speed: int = Field(5, ge=1, le=10)
    volume: int = Field(5, ge=1, le=10)


class VoiceTTSResponse(BaseModel):
    """文字转语音响应"""
    audio_url: str
    duration: float