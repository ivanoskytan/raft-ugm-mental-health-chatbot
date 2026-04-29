from bson import ObjectId
from datetime import datetime, timezone

class Chat:
    def __init__(self, summary, title, excel_file_path, started_at, ended_at, valid=True, user_id=None, _id=None):
        if _id is None:
            self._id = ObjectId()
        else:
            self._id = _id if isinstance(_id, ObjectId) else ObjectId(_id)

        self.title = title
        self.summary = summary
        self.excel_file_path = excel_file_path
        
        if isinstance(started_at, str):
            self.started_at = datetime.fromisoformat(started_at)
        else:
            self.started_at = started_at or datetime.now(timezone.utc)
            
        self.ended_at = ended_at
        self.valid: bool = valid

        if user_id is None:
            self.user_id = None
        else:
            self.user_id = user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)

    def to_dict(self, for_db=False):
        """
        Jika for_db=True, biarkan _id dan user_id dalam bentuk ObjectId.
        Jika False (untuk JSON API), ubah menjadi string.
        """
        if for_db:
            return {
                "_id": self._id,
                "title": self.title,
                "summary": self.summary,
                "valid": self.valid,
                "excel_file_path": self.excel_file_path,
                "started_at": self.started_at,
                "ended_at": self.ended_at,
                "user_id": self.user_id
            }
        
        return {
            "id": str(self._id),  
            "title": self.title,
            "summary": self.summary,
            "valid": self.valid,
            "excel_file_path": self.excel_file_path,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "user_id": str(self.user_id) if self.user_id else None
        }

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        
        id_val = data.get("_id") or data.get("id")
        
        return Chat(
            _id=id_val,
            summary=data.get("summary", ""),
            title=data.get("title", ""),
            excel_file_path=data.get("excel_file_path", ""),
            started_at=data.get("started_at"),
            ended_at=data.get("ended_at"),
            valid=data.get("valid", True),
            user_id=data.get("user_id")
        )