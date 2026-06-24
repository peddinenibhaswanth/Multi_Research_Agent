import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Pydantic model for application settings.
    It automatically reads environment variables.
    """
    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # ChromaDB Settings
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # RAG and Agent Settings
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
    MAX_SOURCES: int = int(os.getenv("MAX_SOURCES", 5))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))

    class Config:
        # This allows Pydantic to read from a .env file if you have one
        # although we are using load_dotenv() explicitly.
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instantiate settings
settings = Settings()

