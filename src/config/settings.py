import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings.

    Prefer an explicit DATABASE_URL. If it's not provided, construct one from
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT and DB_NAME. This makes it easy to
    configure the app via environment variables or a .env file.
    """

    DATABASE_URL: Optional[str] = None

    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    # DB driver: 'psycopg' (psycopg3) or 'psycopg2'
    DB_DRIVER: str = os.getenv("DB_DRIVER", "psycopg2")
    # telegram bot token 

    DOMAIN: str = os.getenv("DOMAIN", "http://localhost:8000")
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_BOT_USERNAME: Optional[str] = os.getenv("TELEGRAM_BOT_USERNAME", "my_garage_service_bot")
    ADMIN_CHAT_ID: Optional[str] = os.getenv("ADMIN_CHAT_ID", "")  # Replace with actual admin chat ID
    # JWT settings (optional - only needed for authentication endpoints)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY", "a_very_secret_key_change_in_production")
    ALGORITHM: str = "HS256"

    # S3/MinIO settings
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "https://fsgw.itedev.online")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "EzFx5KQ4H6QalA0ww6cv")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "4dJQYXt4NQ9aizXiNP8OfBM7Fw0Gda07WO81hy1P")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "garas-fixing")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")

    @model_validator(mode="after")
    def construct_db_url(self):
        """Construct DATABASE_URL from individual components if not provided.
        
        Note: Database connection works independently of SECRET_KEY.
        SECRET_KEY is only required for JWT token generation in auth endpoints.
        """
        # If DATABASE_URL is already provided, keep it.
        if self.DATABASE_URL:
            return self

        # Get values from instance or environment variables
        user = self.DB_USER or os.getenv("DB_USER") or "postgres"  # Default to postgres
        password = self.DB_PASSWORD or os.getenv("DB_PASSWORD")
        host = self.DB_HOST or os.getenv("DB_HOST", "localhost")
        port = self.DB_PORT or int(os.getenv("DB_PORT", 5432))
        db = self.DB_NAME or os.getenv("DB_NAME", "fixing_service_db")
        driver = self.DB_DRIVER or os.getenv("DB_DRIVER", "psycopg2")

        # Construct authentication part
        if password:
            auth = f"{user}:{password}@"
        else:
            auth = f"{user}@"

        self.DATABASE_URL = f"postgresql+{driver}://{auth}{host}:{port}/{db}"
        return self

settings = Settings()
