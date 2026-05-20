from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    LOG_LEVEL: str = "INFO"
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"
    
settings = Settings()
