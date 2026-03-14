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
from services.semantic_search_service import SemanticSearchService


class ChatService:
    """对话业务逻辑"""

    LOCATION_QUERY_TOKENS = (
        "有什么东西",
        "里面有什么",
        "里有什么",
        "有什么",
        "有啥",
    )

    @staticmethod
    def create_session() -> str:
        """创建新会话"""
        return str(uuid.uuid4())

    @staticmethod
    async def chat(db: Session, family_id: int, user_id: int, message: str,
                   session_id: Optional[str] = None) -> dict:
        """处理对话（优先规则提取，大模型兜底）"""
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

        intent, matched_items, reply = ChatService._process_intent(
            db, family_id, message
        )
        
        if intent == "unknown":
            try:
                parsed = await parse_find_intent(message)
                intent, matched_items, reply = ChatService._apply_parsed_intent(
                    db, family_id, parsed
                )
            except Exception:
                pass

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
            items, _ = SemanticSearchService.search_items(db, family_id, keyword, limit=5)
            if items:
                reply = ChatService._format_search_result(items)
                return "search", ChatService._items_to_dict(db, items), reply
            return "search", [], ChatService._get_not_found_reply(keyword, message)

        if intent == "query_expire":
            return "query_expire", [], "这个功能我正在学中📚 不过你可以看看首页的「智能提醒」，那里会告诉你哪些东西快过期啦！😊"

        return "unknown", [], ChatService._get_unknown_intent_reply()

    @staticmethod
    def _process_intent(db: Session, family_id: int, message: str) -> tuple[str, list, str]:
        """规则兜底：DeepSeek 不可用时的关键词匹配"""
        msg = (message or "").strip()

        keyword = ChatService._extract_search_keyword(msg)
        if keyword:
            items, _ = SemanticSearchService.search_items(db, family_id, keyword, limit=5)
            if items:
                reply = ChatService._format_search_result(items)
                return "search", ChatService._items_to_dict(db, items), reply
            return "search", [], ChatService._get_not_found_reply(keyword, message)

        if "过期" in msg:
            return "query_expire", [], "暂未实现过期查询功能"

        return "unknown", [], ChatService._get_unknown_intent_reply()

    @staticmethod
    def _get_unknown_intent_reply() -> str:
        """生成友好的未知意图回复（多种文案随机）"""
        import random
        
        replies = [
            "哎呀，我有点没理解～你可以试试这样问我：剪刀在哪？或者我的护照放哪了？😊",
            "这个问题把我难住了😅 试试问我「XX 在哪里」或者「XX 呢」，我更能听懂哦！",
            "我还没学会这个技能🥺 不过你要是问我东西放哪了，我肯定知道！",
            "让我想想...🤔 要不你换个说法？比如「感冒药在哪」或者「找剪刀」？",
            "这个我暂时还不太懂😳 试试问我「我的钥匙在哪」或者「剪刀呢」？",
        ]
        
        return random.choice(replies)

    @staticmethod
    def _get_not_found_reply(keyword: str, original_message: str) -> str:
        """生成友好的未找到回复（多种文案随机）"""
        import random
        
        # 根据输入方式选择不同的文案风格
        is_short_query = len(original_message.strip()) <= 8  # 简短查询（如"剪刀"、"剪刀呢"）
        
        if is_short_query:
            # 简短查询的友好回复
            replies = [
                f"我帮你找了下，家里没有「{keyword}」哦，要不要再确认下？🤔",
                f"翻遍了角落，没发现「{keyword}」的踪迹，是不是记错啦？🧐",
                f"「{keyword}」好像不在家里呢，看看是不是放外面了？🔍",
                f"没有找到「{keyword}」，要不要换个关键词试试？😊",
                f"我仔细找了找，没看到「{keyword}」，可能藏得比较隐蔽？😅",
            ]
        else:
            # 完整句子的友好回复
            replies = [
                f"我帮你找了一圈，没发现「{keyword}」，要不要再想想放哪了？🤔",
                f"翻遍了所有地方，「{keyword}」好像不在家里呢🧐",
                f"「{keyword}」暂时没找到，是不是最近挪过位置呀？🔍",
                f"没有找到「{keyword}」相关的物品，换个说法试试？😊",
                f"我认真找了，但没找到「{keyword}」，可能藏在某个角落？😅",
            ]
        
        return random.choice(replies)

    @staticmethod
    def _extract_search_keyword(message: str) -> str:
        """提取搜索关键词（灵活识别多种寻物表达方式）"""
        msg = (message or "").strip()
        if not msg:
            return ""

        # 1. 位置疑问句：XXX 在哪/在哪里/放哪/放在哪/位置在哪/...
        if ("在哪" in msg or "在哪里" in msg or "位置" in msg or 
            "放在哪" in msg or "放哪" in msg or "搁哪" in msg):
            keyword = msg
            # 按长度降序替换，避免"在哪"把"放在哪"切坏
            for token in ["在哪里", "放在哪", "放哪", "在哪", "位置", "搁哪"]:
                keyword = keyword.replace(token, "")
            # 再清理常见动词和语气词
            for token in ["放", "了", "啊", "呢", "呀", "嘛"]:
                keyword = keyword.replace(token, "")
            return keyword.strip("？?。！!，,、 ")

        # 2. 容器查询：XX 里有什么/XX 里面有什么
        if any(token in msg for token in ChatService.LOCATION_QUERY_TOKENS):
            keyword = msg
            for token in ChatService.LOCATION_QUERY_TOKENS:
                keyword = keyword.replace(token, "")
            keyword = keyword.replace("里", "").replace("中", "").strip()
            return keyword.strip("？?。！!，,、 ")

        # 3. 简短寻物：单个物品名 + 语气词（剪刀呢？钥匙？药！）
        # 特征：2-6 个字，不包含完整句子结构
        if 1 <= len(msg) <= 8:
            # 清理常见语气词和标点
            keyword = msg.strip("？?。！!，,、呢啊呀嘛哦噢")
            # 如果清理后仍有内容，且不是完整句子（没有主谓宾结构），则认为是寻物
            if keyword and len(keyword) >= 1:
                # 排除明显不是寻物的情况
                if not any(排除词 in keyword for 排除词 in ["是", "有", "要", "想", "能", "会", "应该"]):
                    return keyword

        # 4. 其他常见寻物表达：
        # - "我的 XX"、"XX 在哪里的"、"找 XX"
        if msg.startswith("我的") and len(msg) <= 10:
            return msg[2:].strip("？?。！!，,、呢啊呀嘛")
        
        if msg.startswith("找") and len(msg) <= 10:
            return msg[1:].strip("？?。！!，,、呢啊呀嘛")
        
        if msg.endswith("在哪里的") or msg.endswith("在哪里的？"):
            return msg.replace("在哪里的", "").replace("？", "").strip()

        return ""
    
    @staticmethod
    def _format_search_result(items: List[Item]) -> str:
        """格式化搜索结果（友好自然的文案）"""
        if len(items) == 1:
            item = items[0]
            return f"找到了！📦 {item.name} 在 {item.location}"
        else:
            # 多个结果
            lines = [f"好嘞！找到 {len(items)} 个可能相关的物品：🎉"]
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. {item.name} - {item.location}")
            lines.append("看看有没有你要找的？😊")
            return "\n".join(lines)
    
    @staticmethod
    def _items_to_dict(db: Session, items: List[Item]) -> list:
        """转换为字典（包含 extension 和 category_name）"""
        result = []
        for item in items:
            # 显式加载 extension（如果还没加载）
            if hasattr(item, 'extension') and item.extension is None:
                from sqlalchemy.orm import object_session
                session = object_session(item)
                if session:
                    session.refresh(item, ['extension'])
            
            item_dict = {
                "id": int(item.id),
                "name": item.name,
                "location": item.location,
                "photo_path": item.photo_path,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "score": getattr(item, "semantic_score", None),
                "category_name": getattr(item, "category_name", None),
            }
            # 添加扩展信息（包含过期日期）
            if hasattr(item, 'extension') and item.extension:
                item_dict["extension"] = {
                    "expire_date": item.extension.expire_date.isoformat() if item.extension.expire_date else None,
                    "production_date": item.extension.production_date.isoformat() if item.extension.production_date else None,
                    "shelf_life_days": item.extension.shelf_life_days,
                    "warranty_date": item.extension.warranty_date.isoformat() if item.extension.warranty_date else None,
                }
            result.append(item_dict)
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