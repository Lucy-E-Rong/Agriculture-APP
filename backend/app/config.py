from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_provider: str = "gemini"
    default_language: str = "en"
    demo_access_code: str | None = None

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "scan-images"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"

    local_vlm_url: str = "http://localhost:9000/v1/analyze"
    local_vlm_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
