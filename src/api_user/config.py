from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    LOG_LEVEL: str = "info"
    DEBUG: bool = False
    API_BASE_URL: str = "hpp://fastapi:8000/api"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
