from bson import ObjectId
from datetime import datetime, timezone

class Chat:
    def __init__(self, summary, title, excel_file_path, started_at, ended_at, valid=True, user_id=None, _id=None):
        self._id = _id or ObjectId()
        self.title = title
        self.summary = summary
        self.excel_file_path = excel_file_path
        self.started_at = started_at or datetime.now(timezone.utc)
        self.ended_at = ended_at
        self.valid: bool = valid
        self.user_id = user_id

    def to_dict(self):
        data = vars(self).copy()
        data["_id"] = str(self._id)
        return data

    @staticmethod
    def from_dict(data):
        if not data:
            return None
    
        return Chat(**data)