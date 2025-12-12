"""Configuration management for MedAnnotator."""
import os
from typing import Literal
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google AI Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    # MedGemma Configuration
    medgemma_endpoint: Literal["local", "vertex_ai"] = os.getenv("MEDGEMMA_ENDPOINT", "local")
    medgemma_model_path: str = os.getenv("MEDGEMMA_MODEL_PATH", "google/medgemma-4b")

    # Backend Configuration
    backend_host: str = os.getenv("BACKEND_HOST", "localhost")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    streamlit_port: int = int(os.getenv("STREAMLIT_PORT", "8501"))

    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")

    # Gemini Model Configuration
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
