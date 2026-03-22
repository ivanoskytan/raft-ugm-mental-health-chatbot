from api.model.question_score_model import QuestionScore
from config.config import db
from bson import ObjectId

question_score_collection = db['question_scores']

class QuestionScoreRepository:
    @staticmethod
    def create(section, original_question, score, chat_item_id, group_id):
        question_score = QuestionScore(
            section=section,
            original_question=original_question,
            score=score,
            chat_item_id=chat_item_id,
            group_id=group_id
        )
        question_score_collection.insert_one(question_score.to_dict())
        return question_score

    @staticmethod
    def get_by_id(score_id):
        data = question_score_collection.find_one({"_id": ObjectId(score_id)})
        return QuestionScore.from_dict(data)

    @staticmethod
    def get_by_chat_item(chat_item_id):
        cursor = question_score_collection.find({"chat_item_id": chat_item_id})
        return [QuestionScore.from_dict(item) for item in cursor]

    @staticmethod
    def get_by_group(group_id):
        cursor = question_score_collection.find({"group_id": group_id})
        return [QuestionScore.from_dict(item) for item in cursor]

    @staticmethod
    def update(score_id, **payload):
        result = question_score_collection.update_one(
            {"_id": ObjectId(score_id)},
            {"$set": payload}
        )
        return result.modified_count > 0

    @staticmethod
    def delete_by_chat_item(chat_item_id):
        result = question_score_collection.delete_many({"chat_item_id": chat_item_id})
        return result.deleted_count