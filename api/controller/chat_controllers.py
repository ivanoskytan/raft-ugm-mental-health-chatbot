from flask import Blueprint, request, jsonify
from api.service.chat_service import ChatService
from api.service.user_service import UserService
from api.service.file_service import FileService
from api.service.email_service import EmailService
from chatbot_engine.engine import ChatbotEngine
from api.middleware.auth_middleware import RequireAuth, RequireRoles
import logging

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

chatbot_engine = ChatbotEngine()
logger = logging.getLogger("ChatController")

class ChatController:
    def __init__(self):
        return

    @staticmethod
    @chat_bp.post("/start-new-chat")
    @RequireAuth
    @RequireRoles("user")
    def start_new_chat():
        data = request.get_json()

        user_id = data.get("user_id")
        title = data.get("title", "") 

        if not user_id:
            return jsonify({
                "error": "User ID is required"
            }), 400
        
        try:
            chat, message = ChatService.start_new_chat(user_id=user_id, title=title)

            if not chat:
                return jsonify({
                    "message": message
                }), 400
            
            user = UserService.get_user_detail(user_id=user_id)

            username = user.username if user and hasattr(user, "username") else "Teman"

            opening_ai_response = (
                f"Halo {username}, terima kasih sudah meluangkan waktu untuk berbincang hari ini. "
                "Saya ingin memulai dengan beberapa pertanyaan ringan tentang bagaimana perasaan Anda "
                "belakangan ini. Biasanya Anda lebih nyaman dipanggil siapa?"
            )
            
            data = {
                "chat_id": str(chat._id),
                "title": chat.title,
                "started_at": chat.started_at.isoformat() if chat.started_at else None,
                "opening_ai_response": opening_ai_response
            }

            new_chat_item, message = ChatService.add_chat_item(
                section="",
                type="Opening",
                chat_id=chat._id,
                user_answer="",
                ai_response=opening_ai_response,
            )

            if not new_chat_item:
                return jsonify({
                    "message": message
                }), 400

            return jsonify({
                "message": "[ChatController]: New chat is initiated successfully",
                "data": data
            }), 201

        except Exception as e:
            return jsonify({
                "error": repr(e)
            }), 500

    @chat_bp.post("/process-user-answer")
    @RequireAuth
    @RequireRoles("user")
    def process_user_answer():
        data = request.get_json()
        required_fields = ["group_id", "section", "user_answer", "chat_id",  "assistant_question"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"{field} is required"
                }), 400
            
        try:
            prev_chat_item = ChatService.get_latest_chat_item(data["chat_id"])
            last_assistant_response = ""

            if prev_chat_item and hasattr(prev_chat_item, "ai_response"):
                last_assistant_response = prev_chat_item["ai_response"]

            user_query = {
                "section": data["section"],
                "group_id": data["group_id"],
                "user_answer": data["user_answer"],
                "chat_id": data["chat_id"],
                "prev_assistant_response": last_assistant_response
            }
                    
            engine_response = chatbot_engine.generate_response(user_query)

            is_a_survey = data["section"] not in ["Opening", "Ending"] 
            
            chat_type = "Survey" if is_a_survey else data["section"]
            
            chat_item, message = ChatService.add_chat_item(
                section=data["section"],
                type=chat_type,
                chat_id=data["chat_id"],
                user_answer=data["user_answer"],
                ai_response=engine_response["model"].get("assistant_question", ""),
            )

            if is_a_survey:
                scores = engine_response["model"].get("scores") or []
                for score_item in scores:
                    new_question_score, message = ChatService.add_question_score(
                        chat_item_id=chat_item._id,
                        section=data["section"],
                        group_id=data["group_id"],
                        score=score_item.get("score"),
                        original_question=score_item.get("survey_question"),
                    )
                    if not new_question_score:
                        return jsonify({
                            "message": message
                        }), 400                

            return jsonify({
                "message": "[ChatController]: User answer is processed successfully",
                "data": {
                    "chat_item_id": str(chat_item._id),
                    "section": data["section"],
                    "ai_response": chat_item.ai_response,
                    "next_group_id": engine_response["next_group_id"],
                    "next_section": engine_response["next_section"],
                    "user_answer": data["user_answer"],
                }
            }), 201
    
        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 500
    
    @staticmethod
    @chat_bp.post("/end-chat")
    @RequireAuth
    @RequireRoles("user")
    def end_chat():
        try:
            data = request.get_json()
            chat_id = data["chat_id"]
            user_id = data["user_id"]
            
            chat_data, message = ChatService.get_chat(chat_id)

            if not chat_data:
                return jsonify({
                    "error": message
                }), 404
            
            chat_items, message = ChatService.get_chat_items(chat_id)
            if not chat_items:
                return jsonify({
                    "error": message
                }), 404
            
            assessment_map = []
            for item in chat_items:
                if item.type == "Opening":
                    continue

                question_scores_list = []
                question_scores, message = ChatService.get_question_scores(chat_item_id=item._id)
                if message:
                    return jsonify({
                        "error": message
                    }), 404
                
                for question_score in question_scores:
                    question_scores_list.append({
                        "score": question_score.score,
                        "original_question": question_score.original_question
                    })
                section = item.section

                existing_section = next((s for s in assessment_map if s["section"] == section), None)
                if existing_section:
                    existing_section["questions"].extend(question_scores_list)
                else:
                    assessment_map.append({
                        "section": item.section,
                        "questions": question_scores_list
                    })
            is_file_created, file_path, file_bytes, message = FileService.save_into_excel(assessment_map, chat_id)
            if is_file_created:
                updated_chat, message = ChatService.update_chat(chat_id, {
                    "valid": True,
                    "excel_file_path": file_path
                })
                logger.info(f"Chat {chat_id} is updated with file path: {file_path}")
                if not updated_chat:
                    logger.error(f"Error updating chat {chat_id}")
                    return jsonify({
                        "error": message
                    })
            else:
                return jsonify({
                    "error": message
                }), 500
            
            user_data, message = UserService.get_user_detail(user_id)
            if message:
                logger.error(f"Failed to fetch user data for user {user_id}. Error: {message}")
                return jsonify({
                    "error": message
                }), 404
            
            short_id = chat_id[:6] 
            file_name = f"Hasil Asesmen_{short_id}.xlsx"
            
            is_email_sent, message = EmailService.send_gmail(file_bytes, file_path, file_name, user_data.email)
            logger.info(f"Email sending status for chat {chat_id} to user {user_id} ({user_data.email}): {is_email_sent}, message: {message}")
            
            if not is_email_sent:
                logger.error(f"Failed to send email for chat {chat_id} to user {user_id} ({user_data.email}). Error: {message}")
                return jsonify({
                    "error": message
                }), 500
            
            return jsonify({
                "message": "[ChatController]: File is sent successfully"
            }), 200

        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 500

    @staticmethod
    @chat_bp.get("/<chat_id>")
    @RequireAuth
    @RequireRoles("user")
    def get_chat_detail(chat_id):
        chat, message = ChatService.get_chat(chat_id=chat_id)
        if not chat:
            return jsonify({
                "message": message
            }), 404
            
        return jsonify({
            "message": "[ChatController]: Chat detail is fetched successfully",
            "data": chat
        }), 200
    
    @staticmethod
    @chat_bp.get("/user-chats/<user_id>")
    @RequireAuth
    @RequireRoles("user")
    def get_user_chats(user_id):
        chats, message = ChatService.get_user_chats(user_id=user_id)

        if not chats:
            return jsonify({
                "message": message
            }), 404
        
        return jsonify({
            "message": "[ChatController]: User chats are fetched successfully",
            "data": [chat.to_dict() for chat in chats]
        }), 200
    
         
    @staticmethod
    @chat_bp.post("/aspect-progress")
    @RequireAuth
    @RequireRoles("user")
    def update_aspect_progress():
        data = request.get_json()
        group_id = int(data.get("group_id", 0))
        section = data.get("section", "")
        TOTAL_QUESTIONS = 44

        section_structure = {
            "Depression": 2,
            "Anger": 2,
            "Mania": 4,
            "Anxiety": 2,
            "Somatic": 6,
            "Suicidal": 2,
            "Psychosis": 7,
            "Sleep Disturbance": 1,
            "Memory": 5,
            "Dissociation": 6,
            "Substance Use": 4,
            "Repetitive Thought": 3
        }

        sections = list(section_structure.keys())
        current_idx = sections.index(section) if section in sections else -1
        total_answered = 0
        aspect_progress = []

        for i, sec in enumerate(sections):
            sizes = section_structure[sec]

            if i < current_idx:
                answered = sizes
            elif i == current_idx:
                answered = max(0, min(group_id, sizes))
            else:
                answered = 0

            total_answered += answered

            aspect_progress.append({
                "section": sec,
                "answered": answered,
                "total": sizes,
                "percentage": round((answered / sizes * 100), 1) if sizes > 0 else 0
            })

        total_percentage = round((total_answered/TOTAL_QUESTIONS) * 100)

        data = {
            "aspect_progress": aspect_progress,
            "total_answered": total_answered,
            "total_percentage": total_percentage
        }
        
        return jsonify(
            {
                "message": "[ChatController]: Aspect progress is updated successfully",
                "data": data
            }
        ), 200
    
    @staticmethod
    @chat_bp.put("/<chat_id>")
    @RequireAuth
    @RequireRoles("user")
    def update_chat(chat_id):
        data = request.get_json()
        update_data = {}
        if "title" in data:
            update_data["title"] = data["title"]
        
        if not update_data:
            return jsonify({
                "message": "No valid fields to update"
            }), 400
        
        updated_chat, message = ChatService.update_chat(chat_id, update_data)

        if not updated_chat:
            return jsonify({
                "message": message
            }), 404
        
        return jsonify({
            "message": "[ChatController]: Chat is updated successfully",
            "data": updated_chat.to_dict()
        }), 200

    @staticmethod
    @chat_bp.delete("/<chat_id>")
    @RequireAuth
    @RequireRoles("user")
    def delete_chat(chat_id):
        success, message = ChatService.delete_chat(chat_id)

        if not success:
            return jsonify({
                "message": message
            }), 404
        
        return jsonify({
            "message": "[ChatController]: Chat is deleted successfully"
        }), 200