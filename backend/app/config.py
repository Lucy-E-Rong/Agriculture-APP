from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_provider: str = "gemini"
    default_language: str = "en"
    demo_access_code: str | None = None

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "scan-images"
    supabase_signed_url_ttl_seconds: int = 300

    openai_api_key: str | None = None
    openai_model: str = Field(
        default="gpt-5.6-terra",
        validation_alias=AliasChoices("OPENAI_MODEL", "MODEL"),
    )
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"

    local_vlm_url: str = "http://localhost:9000/v1/analyze"
    local_vlm_api_key: str | None = None

    gcp_project_id: str | None = None
    gcp_project_number: str | None = None
    gcp_service_account_email: str | None = None
    gcp_workload_identity_pool_id: str | None = None
    gcp_workload_identity_pool_provider_id: str | None = None
    gcp_audit_log_id: str | None = None
    vercel: str | None = None
    vercel_env: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
