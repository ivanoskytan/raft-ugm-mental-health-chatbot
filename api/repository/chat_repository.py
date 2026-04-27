from api.model.chat_model import Chat
from config.config import db
from bson import ObjectId
import datetime

chat_collection = db['chats']

class ChatRepository:
    
    @staticmethod
    def create(summary, title, user_id=None, excel_file_path="", started_at=None, ended_at=None, valid=False):
        chat = Chat(summary=summary, title=title, user_id=ObjectId(user_id), excel_file_path=excel_file_path, started_at=started_at, ended_at=ended_at, valid=valid)
        chat_dict = chat.to_dict()
        chat_dict["_id"] = ObjectId(chat_dict["_id"])
        chat_collection.insert_one(chat_dict)
        return chat

    @staticmethod
    def get_by_id(chat_id):
        data = chat_collection.find_one({"_id": ObjectId(chat_id)})
        return Chat.from_dict(data)

    @staticmethod
    def get_all_by_user(user_id, only_valid=False):
        query = {"user_id": ObjectId(user_id)}
        if only_valid:
            query["valid"] = True
            
        cursor = chat_collection.find(query).sort("started_at", 1)
        return [Chat.from_dict(item) for item in cursor]

    @staticmethod
    def update(chat_id, **payload):
        result = chat_collection.update_one(
            {"_id": ObjectId(chat_id)}, 
            {"$set": payload}
        )
        if result.modified_count > 0:
            return ChatRepository.get_by_id(chat_id)
        return None

    @staticmethod
    def delete(chat_id):
        result = chat_collection.delete_one({"_id": ObjectId(chat_id)})
        return result.deleted_count > 0