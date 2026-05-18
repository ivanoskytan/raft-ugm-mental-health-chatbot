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
            "password": self.password,
            "role": self.role,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        
        data = data.copy()
        
        if "id" in data:
            if "_id" not in data:
                data["_id"] = data.pop("id")
            else:
                data.pop("id")

        if "_id" in data:
            if isinstance(data["_id"], str):
                try:
                    data["_id"] = ObjectId(data["_id"])
                except Exception:
                    pass

        if "created_at" in data and isinstance(data["created_at"], str):
            try:
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            except Exception:
                data["created_at"] = None
            
        if "password" not in data:
             data["password"] = ""
             
        return User(**data)