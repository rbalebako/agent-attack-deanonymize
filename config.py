from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API keys
    google_api_key: str
    tavily_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None  # For Google Custom Search backend

    # Search configuration
    search_backend: str = "tavily"  # "tavily" or "google"
    max_search_results: int = 5

    # Agent configuration
    gemini_model: str = "gemini-2.0-flash"
    max_iterations: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
