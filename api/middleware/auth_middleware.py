import jwt
from functools import wraps
from flask import request, jsonify, g
from config.config import Settings

settings = Settings.load()

class RequireAuth:
    def __init__(self, f):
        self.f = f
        wraps(f)(self)

    def __call__(self, *args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({"message": "[AuthMiddleware]: Token is missing or invalid format"}), 401
        
        try:
            payload = jwt.decode(token, settings.JWT_TOKEN, algorithms=["HS256"])

            g.current_user = {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role")
            }
        
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "[AuthMiddleware]: Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "[AuthMiddleware]: Invalid token"}), 401
        
        return self.f(*args, **kwargs)
    
class RequireRoles:
    def __init__(self, allowed_roles):
        if isinstance(allowed_roles, str):
            self.allowed_roles = [allowed_roles]
        else:
            self.allowed_roles = allowed_roles

    def __call__(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, "current_user") or g.current_user is None:
                return jsonify({"message": "[AuthMiddleware]: Authentication required"}), 401
            
            user_role = g.current_user.get("role", "user")

            if user_role not in self.allowed_roles:
                return jsonify({"message": f"[AuthMiddleware]: Forbidden access. Role {user_role} does not have access"}), 403
        
            return f(*args, **kwargs)
        return decorated