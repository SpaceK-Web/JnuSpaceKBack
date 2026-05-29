from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ollama 설정
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_MODEL: str = "gpt-oss:20b"

    # RAG 설정
    CHROMA_DB_PATH: str = "./data/chroma_db"
    MEDICAL_DOCS_PATH: str = "./data/medical_docs"

    # STT 설정
    WHISPER_MODEL_SIZE: str = "small"  # tiny | base | small | medium | large-v3

    # DB 설정
    POSTGRES_USERNAME: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DATABASE: str = "database"
    POSTGRES_HOST: str = "127.0.0.1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
