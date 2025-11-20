from pydantic_settings import BaseSettings
from pydantic import model_validator, PostgresDsn
from dotenv import load_dotenv
from typing import Optional
import os

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

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str = "a_very_secret_key"
    ALGORITHM: str = "HS256"

    @model_validator(mode="after")
    def construct_db_url(self):
        # If DATABASE_URL is already provided, keep it.
        if self.DATABASE_URL:
            return self

        user = self.DB_USER or os.getenv("DB_USER")
        password = self.DB_PASSWORD or os.getenv("DB_PASSWORD")
        host = self.DB_HOST or os.getenv("DB_HOST", "localhost")
        port = self.DB_PORT or int(os.getenv("DB_PORT", 5432))
        db = self.DB_NAME or os.getenv("DB_NAME", "fixing_service_db")
        driver = self.DB_DRIVER or os.getenv("DB_DRIVER", "psycopg2")

        auth = ""
        if user:
            # include password if present
            if password:
                auth = f"{user}:{password}@"
            else:
                auth = f"{user}@"

        self.DATABASE_URL = f"postgresql+{driver}://{auth}{host}:{port}/{db}"
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.DB_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

settings = Settings()
