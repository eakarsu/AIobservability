from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://aiobserve:aiobserve@localhost:5432/aiobserve"
    sync_database_url: str = "postgresql://aiobserve:aiobserve@localhost:5432/aiobserve"
    secret_key: str = "dev-secret-key-change-in-production"
    api_key_header: str = "X-API-Key"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Background scheduler
    drift_detection_interval_minutes: int = 15
    alert_evaluation_interval_seconds: int = 60
    hallucination_scoring_enabled: bool = True

    # SMTP (optional)
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    from_email: str = "alerts@ai-observability.local"

    class Config:
        env_file = ".env"

settings = Settings()
