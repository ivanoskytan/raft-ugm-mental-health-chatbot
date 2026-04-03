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
            "_id": str(self._id),
            "username": self.username,
            "email": self.email,
            "role": self.role
        }

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return User(**data)



        