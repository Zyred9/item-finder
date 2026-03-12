"""
对话服务层
"""
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import json

from models import ChatMessage, Item
from services.item_service import ItemService
from services.llm_service import parse_find_intent


class ChatService:
    """对话业务逻辑"""

    @staticmethod
    def create_session() -> str:
        """创建新会话"""
        return str(uuid.uuid4())

    @staticmethod
    async def chat(db: Session, family_id: int, user_id: int, message: str,
                   session_id: Optional[str] = None) -> dict:
        """处理对话（意图由 DeepSeek 解析，失败时回退到规则）"""
        if not session_id:
            session_id = ChatService.create_session()

        user_msg = ChatMessage(
            family_id=family_id,
            user_id=user_id,
            session_id=session_id,
            role="user",
            content=message
        )
        db.add(user_msg)

        try:
            parsed = await parse_find_intent(message)
            intent, matched_items, reply = ChatService._apply_parsed_intent(
                db, family_id, parsed
            )
        except Exception:
            intent, matched_items, reply = ChatService._process_intent(
                db, family_id, message
            )

        ai_msg = ChatMessage(
            family_id=family_id,
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=reply,
            intent=intent,
            matched_items=json.dumps([i["id"] for i in matched_items]) if matched_items else None
        )
        db.add(ai_msg)
        db.commit()

        return {
            "reply": reply,
            "session_id": session_id,
            "intent": intent,
            "matched_items": matched_items,
            "actions": ChatService._generate_actions(matched_items)
        }

    @staticmethod
    def _apply_parsed_intent(db: Session, family_id: int, parsed: dict) -> tuple[str, list, str]:
        """根据 DeepSeek 解析结果执行查库并生成回复"""
        intent = (parsed.get("intent") or "unknown").strip().lower()
        keyword = (parsed.get("keyword") or "").strip()

        if intent == "search" and keyword:
            items = ItemService.search(db, family_id, keyword, limit=5)
            if items:
                reply = ChatService._format_search_result(items)
                return "search", ChatService._items_to_dict(items), reply
            return "search", [], f"没找到「{keyword}」相关的物品"

        if intent == "query_expire":
            return "query_expire", [], "暂未实现过期查询功能"

        return "unknown", [], "抱歉，我没听懂。你可以问我「某某东西在哪」试试～"

    @staticmethod
    def _process_intent(db: Session, family_id: int, message: str) -> tuple[str, list, str]:
        """规则兜底：DeepSeek 不可用时的关键词匹配"""
        msg = message or ""

        if "在哪" in msg or "在哪里" in msg or "位置" in msg or "放在哪" in msg:
            keyword = msg.replace("在哪", "").replace("在哪里", "").replace("放在哪", "").strip()
            if keyword:
                items = ItemService.search(db, family_id, keyword, limit=5)
                if items:
                    reply = ChatService._format_search_result(items)
                    return "search", ChatService._items_to_dict(items), reply
                return "search", [], f"没找到「{keyword}」相关的物品"

        if "过期" in msg:
            return "query_expire", [], "暂未实现过期查询功能"

        return "unknown", [], "抱歉，我没听懂你的意思。你可以试着问我「某某东西在哪」"
    
    @staticmethod
    def _format_search_result(items: List[Item]) -> str:
        """格式化搜索结果"""
        if len(items) == 1:
            item = items[0]
            return f"📄 {item.name}在{item.location}"
        else:
            lines = [f"找到 {len(items)} 个相关物品："]
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. {item.name} - {item.location}")
            lines.append("你要找哪个？")
            return "\n".join(lines)
    
    @staticmethod
    def _items_to_dict(items: List[Item]) -> list:
        """转换为字典"""
        result = []
        for item in items:
            result.append({
                "id": int(item.id),
                "name": item.name,
                "location": item.location,
                "photo_path": item.photo_path,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })
        return result
    
    @staticmethod
    def _generate_actions(items: list) -> list:
        """生成操作按钮"""
        if not items:
            return []
        
        actions = [
            {"type": "navigate", "label": "📍 导航"},
            {"type": "photo", "label": "📷 查看照片"},
            {"type": "tts", "label": "🔊 播报"}
        ]
        
        if len(items) > 1:
            actions.append({"type": "detail", "label": "📋 查看详情"})
        
        return actions
    
    @staticmethod
    def get_history(db: Session, family_id: int, session_id: str, 
                    limit: int = 50) -> List[ChatMessage]:
        """获取对话历史"""
        return db.query(ChatMessage).filter(
            ChatMessage.family_id == family_id,
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
    
    @staticmethod
    def clear_history(db: Session, family_id: int, session_id: str) -> bool:
        """清空对话历史"""
        deleted = db.query(ChatMessage).filter(
            ChatMessage.family_id == family_id,
            ChatMessage.session_id == session_id
        ).delete()
        db.commit()
        return deleted > 0