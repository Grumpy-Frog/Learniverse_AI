from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Learniverse AI API"
    api_prefix: str = "/api/v1"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    frontend_origin: str = "http://localhost:3000"

    # Keep this harmless setting even if documents are not built yet.
    storage_dir: str = "storage/documents"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    tutor_max_output_tokens: int = 1500
    tutor_scope_check_max_tokens: int = 5
    deepseek_min_balance: float = 2.00
    deepseek_balance_currency: str = "USD"
    deepseek_balance_check_enabled: bool = True
    deepseek_request_timeout_seconds: float = 45.0

    diagnostic_quiz_output_tokens: int = 1800
    diagnostic_evaluation_output_tokens: int = 350
    diagnostic_pass_percentage: float = 80.0

    remediation_generation_output_tokens: int = 1400
    remediation_evaluation_output_tokens: int = 400
    remediation_pass_score: float = 0.7

    blog_validation_output_tokens: int = 300
    blog_generation_output_tokens: int = 2500

    storage_dir: str = "storage/documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()