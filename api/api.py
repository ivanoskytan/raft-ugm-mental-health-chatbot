from flask import Blueprint
from api.controller.chat_controllers import chat_bp
from api.controller.auth_controllers import auth_bp
from api.controller.admin_controllers import admin_bp
from api.controller.user_controllers import user_bp

class APIModule:
    def __init__(self):
        self.blueprint = Blueprint(
            "api",
            __name__,
            url_prefix="/api"
        )

    def register_routes(self):
        self.blueprint.register_blueprint(chat_bp)
        self.blueprint.register_blueprint(auth_bp)
        self.blueprint.register_blueprint(admin_bp)
        self.blueprint.register_blueprint(user_bp)