from bson import ObjectId
from datetime import datetime, timezone

class User:
    def __init__(self, username, email, password, role, _id=None, created_at=None):
        self._id = _id or ObjectId()
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self):
        return vars(self)

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        if "_id" in data and isinstance(data["_id"], str):
            data["_id"] = ObjectId(data["_id"])
        return User(**data)


        