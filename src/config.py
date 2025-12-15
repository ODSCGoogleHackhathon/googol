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
    medgemma_endpoint: Literal["mock", "huggingface", "vertex_ai", "cloud_api"] = os.getenv(
        "MEDGEMMA_ENDPOINT", "huggingface"
    )
    medgemma_model_id: str = os.getenv("MEDGEMMA_MODEL_ID", "google/medgemma-4b-it")
    medgemma_cache_dir: str = os.getenv("MEDGEMMA_CACHE_DIR", "./models")
    medgemma_device: str = os.getenv("MEDGEMMA_DEVICE", "auto")  # "auto", "cpu", "cuda", "mps"
    huggingface_token: str = os.getenv("HUGGINGFACE_TOKEN", "")  # Optional, for private models
    medgemma_cloud_api_url: str = os.getenv("MEDGEMMA_CLOUD_API_URL", "")
    medgemma_cloud_api_timeout: int = int(os.getenv("MEDGEMMA_CLOUD_API_TIMEOUT", "600"))

    # Backend Configuration
    backend_host: str = os.getenv("BACKEND_HOST", "localhost")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    streamlit_port: int = int(os.getenv("STREAMLIT_PORT", "8501"))

    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")

    # Gemini Model Configuration
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048

    # Gemini Enhancement Features
    enable_gemini_enhancement: bool = (
        os.getenv("ENABLE_GEMINI_ENHANCEMENT", "true").lower() == "true"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
