from functools import lru_cache
from app.llm.base import LLMProvider
from app.llm.config import LLMSettings, LLMFallbackSettings
from app.llm.factory import create_llm_provider
from app.llm.fallback import FallbackLLMProvider


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()


@lru_cache
def get_llm_fallback_settings() -> LLMFallbackSettings:
    return LLMFallbackSettings()


@lru_cache
def get_llm_provider() -> LLMProvider:
    primary = create_llm_provider(get_llm_settings())
    secondary = create_llm_provider(get_llm_fallback_settings())
    return FallbackLLMProvider(primary, secondary)