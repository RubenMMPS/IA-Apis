from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class LLMSettings(BaseSettings):
    provider: Literal["gemini", "groq"] = "groq"
    api_key: str
    model_name: str

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        protected_namespaces=(),
        extra="ignore",
    )

class LLMFallbackSettings(BaseSettings):
    provider: Literal["gemini", "groq"] = "gemini"
    api_key: str
    model_name: str

    model_config = SettingsConfigDict(
        env_prefix="LLM_FALLBACK_",
        env_file=".env",
        protected_namespaces=(),
        extra="ignore",
    )