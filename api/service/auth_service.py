import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from api.repository.user_repository import UserRepository

class AuthService:

    @staticmethod
    def register(username: str, email: str, password: str, role: str):
        existing = UserRepository.find_by_email(email)

        if existing:
            return False, "[AuthService]: User already exists"

        hashed = generate_password_hash(password)

        try:
            UserRepository.create(username, email, hashed, role)
            return True, None
        except Exception:
            return False, "[AuthService]: Failed to create user"

    @staticmethod
    def login(email: str, password: str, secret_key: str):
        user = UserRepository.find_by_email(email)

        if not user or not check_password_hash(user.password, password):
            return None, "[AuthService]: Invalid email or password"

        payload = {
            "user_id": str(user._id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
        }

        token = jwt.encode(payload, secret_key, algorithm="HS256")

        data = {
            "user_id": str(user._id),
            "token": token,
        }
        
        return data, None
