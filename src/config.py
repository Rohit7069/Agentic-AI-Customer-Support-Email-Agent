"""Application configuration loaded from environment variables."""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./email_agent.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # FAISS Knowledge Base
    KB_INDEX_PATH: str = "./data/faiss_index"
    KB_DOCUMENTS_PATH: str = "./data/kb_documents.json"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
