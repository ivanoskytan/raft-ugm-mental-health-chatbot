from datetime import datetime
from api.repository.chat_repository import ChatRepository
from api.repository.user_repository import UserRepository
from api.repository.question_score_repository import QuestionScoreRepository

class AdminService:
    @staticmethod
    def get_all_valid_chats(user_id: str):
        valid_chats = ChatRepository.get_all_by_user(user_id)
        if not valid_chats:
            return [], "[AdminService]: No valid chats found for this user"
         
        return valid_chats, None
    
    @staticmethod
    def get_all_users():
        all_users = UserRepository.get_all()
        if not all_users:
            return [], "[AdminService]: No users found"
        
        return all_users, None
    
    @staticmethod
    def get_user_assesments(chat_id: str):
        return ChatRepository.get_by_id(chat_id)
    
    @staticmethod
    def get_real_time_assessment_results(aspect, start_time: datetime, end_time: datetime):
        return QuestionScoreRepository.get_average_scores_by_date(aspect, start_time, end_time)
    
    @staticmethod
    def get_top_scored_users(aspect, start_time: datetime, end_time: datetime, top_k: int):
        return QuestionScoreRepository.get_top_scored_users(aspect, start_time, end_time, top_k)