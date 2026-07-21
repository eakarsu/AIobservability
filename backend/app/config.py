import json

from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    sync_database_url: str
    secret_key: str
    api_key_header: str = "X-API-Key"
    cors_origins: str

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

    @field_validator("secret_key")
    @classmethod
    def secure_secret(cls, value: str) -> str:
        if len(value) < 32: raise ValueError("SECRET_KEY must be at least 32 characters")
        return value

    @property
    def parsed_cors_origins(self) -> list[str]:
        value = self.cors_origins.strip()
        if value.startswith("["):
            parsed = json.loads(value)
            if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                raise ValueError("CORS_ORIGINS JSON must be a list of strings")
            return parsed
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
