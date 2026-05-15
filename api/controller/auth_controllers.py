from flask import Blueprint, request, jsonify
from api.service.auth_service import AuthService
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

SECRET_KEY = os.getenv("JWT_SECRET", "default-secret-change-this")

class AuthController:
    @staticmethod
    @auth_bp.post("/register")
    def register():
        data = request.get_json() or {}

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        role = data.get("role", "user")

        if not email or not password:
            return jsonify({"message": "[AuthController]: Email and password are required"}), 400
        
        if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            return jsonify({"message": "[AuthController]: Password must be at least 8 characters long and contain both letters and numbers"}), 400

        success, message = AuthService.register(username, email, password, role)

        if not success:
            return jsonify({"message": message}), 409

        return jsonify({"message": "[AuthController]: User registered successfully"}), 201

    @staticmethod
    @auth_bp.post("/login")
    def login():
        data = request.get_json() or {}

        email = data.get("email", "").strip()
        role = data.get("role", "")
        password = data.get("password", "")

        if not email or not password or not role:
            return jsonify({"message": "[AuthController]: Email, role, and password are required"}), 400
        
        data, error = AuthService.login(email, role, password, SECRET_KEY)

        if error:
            return jsonify({"message": error}), 401

        return jsonify({
            "message": "[UserController]: Login successful",
            "data": data
        }), 200
