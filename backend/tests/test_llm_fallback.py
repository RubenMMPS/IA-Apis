from app.llm.base import LLMProvider
from app.llm.fallback import FallbackLLMProvider
from app.llm.models import LLMRequest, LLMMessage, LLMResponse, LLMUsage
from app.llm.exceptions import LLMProviderError, LLMResponseParsingError, is_retryable_error


def make_request() -> LLMRequest:
    return LLMRequest(messages=[LLMMessage(role="user", content="hola")])


def make_response(text: str) -> LLMResponse:
    return LLMResponse(
        content=text, model="fake", usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        finish_reason="stop",
    )


class FakeProvider(LLMProvider):
    def __init__(self, behavior):
        self.behavior = behavior
        self.called = False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.called = True
        if isinstance(self.behavior, Exception):
            raise self.behavior
        return self.behavior


async def test_primary_success_no_fallback():
    primary = FakeProvider(make_response("ok primario"))
    secondary = FakeProvider(make_response("ok secundario"))
    provider = FallbackLLMProvider(primary, secondary)

    result = await provider.generate(make_request())

    assert result.content == "ok primario"
    assert secondary.called is False


async def test_primary_429_falls_back_to_secondary():
    primary = FakeProvider(LLMProviderError("rate limit 429", retryable=True))
    secondary = FakeProvider(make_response("ok secundario"))
    provider = FallbackLLMProvider(primary, secondary)

    result = await provider.generate(make_request())

    assert result.content == "ok secundario"
    assert secondary.called is True


async def test_primary_503_falls_back_to_secondary():
    primary = FakeProvider(LLMProviderError("503 UNAVAILABLE", retryable=True))
    secondary = FakeProvider(make_response("ok secundario"))
    provider = FallbackLLMProvider(primary, secondary)

    result = await provider.generate(make_request())

    assert result.content == "ok secundario"


async def test_both_providers_fail_raises_clear_error():
    primary = FakeProvider(LLMProviderError("429 primario", retryable=True))
    secondary = FakeProvider(LLMProviderError("503 secundario", retryable=True))
    provider = FallbackLLMProvider(primary, secondary)

    try:
        await provider.generate(make_request())
        assert False, "debía lanzar excepción"
    except LLMProviderError as e:
        assert "primario" in str(e) and "secundario" in str(e)


async def test_non_retryable_error_does_not_trigger_fallback():
    primary = FakeProvider(LLMProviderError("400 invalid request", retryable=False))
    secondary = FakeProvider(make_response("no debería llamarse"))
    provider = FallbackLLMProvider(primary, secondary)

    try:
        await provider.generate(make_request())
        assert False, "debía propagar el error del primario"
    except LLMProviderError:
        pass

    assert secondary.called is False


async def test_parsing_error_does_not_trigger_fallback():
    primary = FakeProvider(LLMResponseParsingError("respuesta corrupta"))
    secondary = FakeProvider(make_response("no debería llamarse"))
    provider = FallbackLLMProvider(primary, secondary)

    try:
        await provider.generate(make_request())
        assert False, "debía propagar el error de parseo"
    except LLMResponseParsingError:
        pass

    assert secondary.called is False


def test_is_retryable_error_detects_common_patterns():
    assert is_retryable_error("Error code: 429 - rate limit exceeded")
    assert is_retryable_error("503 UNAVAILABLE. This model is currently overloaded")
    assert is_retryable_error("RESOURCE_EXHAUSTED: quota exceeded")
    assert not is_retryable_error("400 INVALID_ARGUMENT: bad request")
    assert not is_retryable_error("API key not valid")