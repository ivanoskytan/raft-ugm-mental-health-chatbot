import os
from dataclasses import dataclass
from pymongo import MongoClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass(frozen=True)
class Settings:
    MONGO_URI: str
    MONGO_DB_NAME: str

    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USE_SSL: bool
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_DEFAULT_SENDER: str
    MAIL_SUPPRESS_SEND: bool
    MAIL_DEBUG: bool

    OPENAI_API_KEY: str
    FINE_TUNED_MODEL: str

    JWT_TOKEN: str
    ENV: str
    VECTORSTORE_URL: str
    VECTORSTORE_KEY: str

    @classmethod
    def load(cls):
        mongo_uri = os.getenv("MONGO_URI")
        mongo_db_name = os.getenv("MONGO_DB_NAME")

        mail_server = os.getenv("MAIL_SERVER")
        mail_port = os.getenv("MAIL_PORT")
        mail_use_ssl = os.getenv("MAIL_USE_SSL")
        mail_username = os.getenv("MAIL_USERNAME")
        mail_password = os.getenv("MAIL_PASSWORD")
        mail_default_sender = os.getenv("MAIL_DEFAULT_SENDER")
        mail_suppress_send = os.getenv("MAIL_SUPPRESS_SEND")
        mail_debug = os.getenv("MAIL_DEBUG")

        openai_api_key = os.getenv("OPENAI_API_KEY")
        fine_tuned_model = os.getenv("FINE_TUNED_MODEL")

        jwt_token = os.getenv("JWT_TOKEN")
        env = os.getenv("ENV")
        vectorstore_url = os.getenv("VECTORSTORE_URL")
        vectorstore_key = os.getenv("VECTORSTORE_KEY")

        missing = [
            name for name, value in {
                "MONGO_URI": mongo_uri,
                "MONGO_DB_NAME": mongo_db_name,
                "MAIL_SERVER": mail_server,
                "MAIL_PORT": mail_port,
                "MAIL_USE_SSL": mail_use_ssl,
                "MAIL_USERNAME": mail_username,
                "MAIL_PASSWORD": mail_password,
                "MAIL_DEFAULT_SENDER": mail_default_sender,
                "MAIL_SUPPRESS_SEND": mail_suppress_send,
                "MAIL_DEBUG": mail_debug,
                "OPENAI_API_KEY": openai_api_key,
                "FINE_TUNED_MODEL": fine_tuned_model,
                "JWT_TOKEN": jwt_token,
                "ENV": env,
                "VECTORSTORE_URL": vectorstore_url,
                "VECTORSTORE_KEY": vectorstore_key
            }.items()
            if value is None or value == ""
        ]

        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            MONGO_URI=mongo_uri,
            MONGO_DB_NAME=mongo_db_name,
            MAIL_SERVER=mail_server,
            MAIL_PORT=int(mail_port),
            MAIL_USE_SSL=mail_use_ssl.lower() == "true",
            MAIL_USERNAME=mail_username,
            MAIL_PASSWORD=mail_password,
            MAIL_DEFAULT_SENDER=mail_default_sender,
            MAIL_SUPPRESS_SEND=mail_suppress_send.lower() == "true",
            MAIL_DEBUG=mail_debug.lower() == "true",
            OPENAI_API_KEY=openai_api_key,
            FINE_TUNED_MODEL=fine_tuned_model,
            JWT_TOKEN=jwt_token,
            ENV=env,
            VECTORSTORE_URL=vectorstore_url,
            VECTORSTORE_KEY=vectorstore_key,
        )


settings = Settings.load()

mongo_client = MongoClient(settings.MONGO_URI)
db = mongo_client[settings.MONGO_DB_NAME]
