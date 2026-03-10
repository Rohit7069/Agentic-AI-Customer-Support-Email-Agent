"""Application configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Explicitly set LangChain environment variables EARLY for the tracer
if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    # Ensure they are in os.environ for LangChain/LangSmith tracer
    for key in ["LANGCHAIN_ENDPOINT", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT", "OPENAI_API_KEY"]:
        val = os.getenv(key)
        if val:
            os.environ[key] = val

from pydantic_settings import BaseSettings


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

    # LangSmith Monitoring (Optional)
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "email-agent-demo"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
