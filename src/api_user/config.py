from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    LOG_LEVEL: str = "info"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra = "ignore",
    )


settings = Settings()
