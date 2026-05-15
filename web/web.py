from flask import Blueprint, render_template

class WebModule:
    def __init__(self):
        self.blueprint = Blueprint(
            "web",
            __name__,
            static_folder="static",
            static_url_path="/web/static",
            template_folder="view",
        )

    def register_pages(self):
        @self.blueprint.route("/admin")
        def admin_page():
            return render_template("admin.html")
        
        @self.blueprint.route("/dashboard/user")
        def admin_dashboard_user_page():
            return render_template("dashboard.html")
        
        @self.blueprint.route("/register")
        def register_page():
            return render_template("register.html")
        
        @self.blueprint.route("/login")
        def login_page():
            return render_template("login.html")
        
        @self.blueprint.route("/chat")
        def chat_page():
            return render_template("chat.html")
        
        @self.blueprint.route("/admin/login")
        def admin_login_page():
            return render_template("admin_login.html")