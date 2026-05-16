from flask import Blueprint, request, jsonify
from api.service.user_service import UserService

user_bp = Blueprint("user", __name__, url_prefix="/user")

class ChatController:
    def __init__(self):
        return

    @staticmethod
    @user_bp.get("/<user_id>")
    def get_user_profile(user_id):
        if not user_id:
            return jsonify({
                "message": "[UserController]: User ID is required"
            }), 400
        
        user_profile, error = UserService.get_user_detail(user_id)

        if error:
            return jsonify({
                "error": error
            }), 404
        
        return jsonify({
            "message": "[UserController]: User profile retrieved successfully",
            "data": user_profile.to_dict()
        }), 200
