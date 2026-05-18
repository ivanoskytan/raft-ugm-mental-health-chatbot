from api.model.user_model import User
from config.config import db
from bson import ObjectId

users_collection = db['users']

class UserRepository:
    @staticmethod
    def create(username, email, password, role):
        user = User(
            username=username,
            email=email,
            password=password,
            role=role
        )
        users_collection.insert_one(user.to_dict())
        return user

    @staticmethod
    def get_by_id(user_id):
        data = users_collection.find_one({"_id": ObjectId(user_id)})
        return User.from_dict(data)

    @staticmethod
    def find_by_email(email):
        data = users_collection.find_one({"email": email})
        return User.from_dict(data)

    @staticmethod
    def get_all(query=None):
        mongo_query = {}

        if query:
            if "username" in query and query["username"]:
                mongo_query["username"] = {"$regex": query["username"], "$options": "i"}
            if "email" in query and query["email"]:
                mongo_query["email"] = {"$regex": query["email"], "$options": "i"}

        cursor = users_collection.find(mongo_query)

        return [User.from_dict(item) for item in cursor]

    @staticmethod
    def update(user_id, **payload):
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": payload}
        )
        return result.modified_count > 0

    @staticmethod
    def delete(user_id):
        result = users_collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0