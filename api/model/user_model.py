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
        return {
            "_id": ObjectId(self._id),  
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "role": self.role,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        if "_id" in data and isinstance(data["_id"], str):
            data["_id"] = ObjectId(data["_id"])
        if "password" not in data:
             data["password"] = ""
        return User(**data)


        