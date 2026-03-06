from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"

    MATCH_TIMEOUT: int = 30        # seconds to wait for a match
    QUEUE_CLEANUP_INTERVAL: int = 60  # seconds between queue cleanups

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
