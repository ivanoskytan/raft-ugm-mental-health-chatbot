from api.repository.user_repository import UserRepository

class UserService:
    @staticmethod
    def get_user_detail(user_id):
        user = UserRepository.get_by_id(user_id)

        if not user:
            return None, "[UserService]: User not found"

        return user, None