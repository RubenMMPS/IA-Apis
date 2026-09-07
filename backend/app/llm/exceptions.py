import re

class LLMServiceError(Exception):
    pass


class LLMProviderError(LLMServiceError):
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class LLMResponseParsingError(LLMServiceError):
    pass


_RETRYABLE_PATTERNS = [
    r"\b429\b", r"\b503\b", r"rate.?limit", r"UNAVAILABLE",
    r"RESOURCE_EXHAUSTED", r"overloaded", r"timeout",
]


def is_retryable_error(message: str) -> bool:
    return any(re.search(p, message, re.IGNORECASE) for p in _RETRYABLE_PATTERNS)