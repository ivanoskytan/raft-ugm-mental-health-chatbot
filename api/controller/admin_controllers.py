from api.service.admin_service import AdminService
from flask import Blueprint, request, jsonify, send_file, abort
import os
import json

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

class AdminController:
    @staticmethod
    @admin_bp.get("/all-valid-chats/<user_id>")
    def get_all_chats(user_id):
        try:
            chats, message = AdminService.get_all_chats(user_id)
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
            search_query = request.args.to_dict()

            users, message = AdminService.get_all_users(query=search_query)
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
        
    @staticmethod
    @admin_bp.post("/real-time-assessment-results")
    def get_real_time_assessment_results():
        data = request.get_json()

        aspect = data.get("aspect")
        from_date = data.get("from_date")
        to_date = data.get("to_date")

        if aspect not in ["Depression", "Anger", "Mania", "Anxiety", "Somatic", "Suicidal", "Psychosis", "Sleep Disturbance", "Memory", "Dissociation", "Substance Use"]:
            return jsonify({"error": "Invalid aspect provided."}), 400

        if not from_date or not to_date:
            return jsonify({"error": "Both from_date and to_date are required."}), 400
        
        BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
        grouped_questions_dir = os.path.join(BASE_DIR, "external_data", "grouped_mental_health_screening.json")
        
        with open(grouped_questions_dir, "r", encoding="utf-8") as f:
            grouped_questions = json.load(f)
        
        for item in grouped_questions:
            if item["section"] == aspect:
                scoring_system = item.get("scoring_system", [])
                break

        try:
            results = AdminService.get_real_time_assessment_results(aspect, from_date, to_date)
            data = {
                "results": results,
                "score_distributions": scoring_system
            }
            return jsonify({"data": data}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500  
        
    @staticmethod
    @admin_bp.post("/top-scored-users")
    def get_top_scored_users():
        data = request.get_json()

        aspect = data.get("aspect")
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        top_k = data.get("top_k")

        if aspect not in ["Depression", "Anger", "Mania", "Anxiety", "Somatic", "Suicidal", "Psychosis", "Sleep Disturbance", "Memory", "Dissociation", "Substance Use"]:
            return jsonify({"error": "Invalid aspect provided."}), 400

        if not from_date or not to_date:
            return jsonify({"error": "Both from_date and to_date are required."}), 400
        
        try:
            results = AdminService.get_top_scored_users(aspect, from_date, to_date, top_k)
            return jsonify({"data": results}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500  