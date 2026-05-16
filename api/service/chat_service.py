from datetime import datetime
from api.repository.chat_repository import ChatRepository
from api.repository.chat_item_repository import ChatItemRepository
from api.repository.question_score_repository import QuestionScoreRepository


class ChatService:
    @staticmethod
    def start_new_chat(user_id, title):
        try:
            chat = ChatRepository.create(
                summary="",
                started_at=datetime.utcnow(),
                ended_at=None,
                title=title,
                excel_file_path="",
                valid=False,
                user_id=user_id
            )

            return chat, None
        
        except Exception as e:
            return None, f"[ChatService]: Failed to start chat - {e}"
    
    @staticmethod
    def add_chat_item(
        chat_id,
        type,
        user_answer=None,
        ai_response=None,
        section=None
    ):
        try:
            chat_item = ChatItemRepository.create(
                user_answer=user_answer,
                ai_response=ai_response,
                type=type,
                chat_id=chat_id,
                section=section,
            )
            return chat_item, None

        except Exception as e:
            return None, f"[ChatService]: Failed to add chat item- {e}"
    
    @staticmethod
    def get_chat_items(
        chat_id
    ):
        try:
            chat_items = ChatItemRepository.get_all_by_chat(
                chat_id
            )

            if not chat_items:
                return None, "[ChatService]: Chat items not found"
            
            return chat_items, None

        except Exception as e:
            return None, f"[ChatService]: Failed to retrieve chat items - {e}"
        
    @staticmethod
    def get_question_scores(
        chat_item_id
    ):
        try:
            question_scores = QuestionScoreRepository.get_by_chat_item(
                chat_item_id
            )

            if not question_scores:
                return None, "[ChatService]: Question scores not found"
            
            return question_scores, None
        except Exception as e:
            return None, f"[ChatService]: Failed to retrieve question scores - {e}"
    
    @staticmethod
    def add_question_score(
        section,
        original_question,
        score,
        chat_item_id,
        group_id=None
    ):
        try:
            question_score = QuestionScoreRepository.create(
                section=section,
                original_question=original_question,
                score=score,
                chat_item_id=chat_item_id,
                group_id=group_id
            )
            return question_score, None
        
        except Exception as e:
            return None, f"[ChatService]: Failed to add question score - {e}"
    
    
    @staticmethod
    def get_chat(chat_id):
        chat =  ChatRepository.get_by_id(chat_id)
        
        if not chat:
            return None, "[ChatService]: Chat not found"
        
        return chat, None
    
    @staticmethod
    def get_latest_chat_item(chat_id):
        latest_chat_item = ChatItemRepository.get_latest_item(chat_id)
        
        if not latest_chat_item:
            return None, "[ChatService]: No chat items found"
        
        return latest_chat_item, None
    
    @staticmethod
    def get_user_chats(user_id):
        user_chats = ChatRepository.get_all_by_user(user_id, only_valid=False)

        if not user_chats:
            return [], "[ChatService]: No chats found for user"
        
        return user_chats, None
    
    @staticmethod
    def update_chat(chat_id, data):
        updated_chat = ChatRepository.update(chat_id, **data)

        if not updated_chat:
            return [], "[ChatService]: Failed to update chat"
        
        return updated_chat, None

    @staticmethod
    def delete_chat(chat_id):
        success = ChatRepository.delete(chat_id)

        if not success:
            return False, "[ChatService]: Failed to delete chat"
        
        return True, None
    
    