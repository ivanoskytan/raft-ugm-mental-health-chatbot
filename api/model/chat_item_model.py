from datetime import datetime, timezone
from bson import ObjectId

class ChatItem:
    def __init__(self, _id=None, type=None, ai_response=None, section=None, chat_id=None, user_answer=None, created_at=None):
        self._id = _id or ObjectId()
        self.type = type
        self.user_answer = user_answer
        self.section = section
        self.ai_response = ai_response
        self.chat_id = chat_id
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self):
        return vars(self)

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return ChatItem(
            _id=data.get("_id"),
            type=data.get("type"),
            ai_response=data.get("ai_response"),
            section=data.get("section"),
            chat_id=data.get("chat_id"),
            user_answer=data.get("user_answer"),
            created_at=data.get("created_at"),
        )