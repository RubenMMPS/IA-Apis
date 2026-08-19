from functools import lru_cache

from app.llm.base import LLMProvider
from app.llm.config import LLMSettings
from app.llm.factory import create_llm_provider


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_llm_settings()
    return create_llm_provider(settings)