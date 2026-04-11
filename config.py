from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Google / Gemini (required when LLM_BACKEND=google)
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None  # For Google Custom Search backend

    # Ollama (required when LLM_BACKEND=ollama)
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"

    # LLM backend selection
    llm_backend: str = "google"  # "google" or "ollama"

    # Active Gemini model (used when llm_backend=google)
    gemini_model: str = "gemini-2.0-flash"

    # Search configuration
    search_backend: str = "tavily"  # "tavily" or "google"
    max_search_results: int = 5
    tavily_api_key: Optional[str] = None

    # Agent configuration
    max_iterations: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
