from app.llm.base import LLMProvider
from app.llm.config import LLMSettings
from app.llm.providers.groq import GroqProvider
from app.llm.providers.gemini import GeminiProvider
from app.llm.exceptions import LLMServiceError


def create_llm_provider(settings: LLMSettings) -> LLMProvider:
    match settings.provider:
        case "groq":
            return GroqProvider(
                api_key=settings.api_key,
                model_name=settings.model_name,
            )
        case "gemini":
            return GeminiProvider(
                api_key=settings.api_key,
                model_name=settings.model_name,
            )
        case _:
            raise LLMServiceError(
                f"Proveedor LLM desconocido: '{settings.provider}'"
            )