from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM 설정
    LLM_PROVIDER: str = "ollama"  # "openai" 또는 "ollama"
    OPENAI_API_KEY: str = Field(default="")  # 선택사항
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    # DB 설정
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "senior_care"
    REDIS_URL: str = "redis://localhost:6379/0"
    POSTGRES_USERNAME: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DATABASE: str = "database"
    POSTGRES_HOST: str = "127.0.0.1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
