from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    LOG_LEVEL: str = "info"
    DEBUG: bool = False
    API_BASE_URL: str = "http://fastapi:8000/api"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
