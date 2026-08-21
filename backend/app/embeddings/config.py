from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingSettings(BaseSettings):
    provider: str = "gemini"
    api_key: str
    model_name: str = "gemini-embedding-001"

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDING_",
        env_file=".env",
        protected_namespaces=(),
        extra="ignore",  
    )   