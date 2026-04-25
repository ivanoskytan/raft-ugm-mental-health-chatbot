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
    
    @staticmethod
    def get_average_scores_by_date(aspect, start_time, end_time):
        pipeline = [
            {
                "$match": {
                    "section": aspect,
                    "created_at": {
                        "$gte": start_time,
                        "$lte": end_time
                    }
                }
            },
            {
                "$lookup": {
                    "from": "chat_items",
                    "localField": "chat_item_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            {
                "$unwind": "$item"
            },
            {
                "$lookup": {
                    "from": "chats",
                    "localField": "item.chat_id",
                    "foreignField": "_id",
                    "as": "chat"
                }
            },
            {
                "$unwind": "$chat"
            },
            {
                "$group": {
                    "_id": "$chat.user_id",
                    "user_avg": {
                        "$avg": "$score"
                    }
                }
            },
            {
                "$project": {
                    "rounded_score": {
                        "$round": ["$user_avg", 0]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$rounded_score",
                    "user_count": {
                        "$sum": 1
                    }
                }
            },
            {
                "$sort": {
                    "_id": 1
                }
            }
        ]

        return list(question_score_collection.aggregate(pipeline))
    
    @staticmethod
    def get_top_scored_users(aspect, start_time, end_time, top_k):
        pipeline = [
            {"$match": {"section": aspect, "created_at": {"$gte": start_time, "$lte": end_time}}},
            {"$lookup": {"from": "chat_items", "localField": "chat_item_id", "foreignField": "_id", "as": "item"}},
            {"$unwind": "$item"},
            {"$lookup": {"from": "chats", "localField": "item.chat_id", "foreignField": "_id", "as": "chat"}},
            {"$unwind": "$chat"},
            {
                "$group": {
                    "_id": "$chat.user_id",
                    "average_score": { "$avg": "$score" }
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user_details"
                }
            },
            {"$unwind": "$user_details"},
            {"$sort": {"average_score": -1}},
            {"$limit": top_k},
            {
                "$project": {
                    "username": "$user_details.username",
                    "email": "$user_details.email",
                    "average_score": 1
                }
            }
        ]
        return list(question_score_collection.aggregate(pipeline))