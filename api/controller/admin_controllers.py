from api.service.admin_service import AdminService
from flask import Blueprint, request, jsonify, send_file, abort
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

class AdminController:
    @staticmethod
    @admin_bp.get("/all-valid-chats/<user_id>")
    def get_all_valid_chats(user_id):
        try:
            chats, message = AdminService.get_all_valid_chats(user_id)
            if not chats:
                return jsonify({
                    "message": message
                }), 404
            chat_list = [chat.to_dict() for chat in chats]
            return jsonify({
                "data": chat_list
            }), 200
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    @admin_bp.get("/all-users")
    def get_all_users():
        try:
            users, message = AdminService.get_all_users()
            if not users:
                return jsonify({
                    "message": message
                }), 404
            
            user_list = [user.to_dict() for user in users]
            return jsonify({
                "data": user_list
            }), 200
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    @admin_bp.get("/user-assessments")
    def get_user_assessments():
        try:
            user_id = request.args.get("user_id")
            assessments = AdminService.get_user_assesments(user_id)
            assessment_list = [assessment.to_dict() for assessment in assessments]
            return jsonify({"data": assessment_list}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    @admin_bp.post("/download-excel")
    def download_excel():
        data = request.get_json()

        try:
            BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            excel_file_path = os.path.join(BASE_DIR, "external_data", "Joy Ivan_report.xlsx")

            if os.path.exists(excel_file_path):
                return send_file(
                    excel_file_path,
                    as_attachment=True,
                    download_name="Joy_Ivan_report.xlsx"
                )
            else:
                return abort(404, description="Excel file not found on server.")
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500