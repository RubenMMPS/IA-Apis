class LLMServiceError(Exception):
    """Error base del servicio LLM, agnóstico de proveedor."""

class LLMProviderError(LLMServiceError):
    """El proveedor devolvió un error (rate limit, API key inválida, etc.)."""

class LLMResponseParsingError(LLMServiceError):
    """La respuesta del proveedor no se pudo mapear a LLMResponse."""