# Precios aproximados en USD por cada 1M de tokens. Solo para estimación orientativa,
# no reflejan facturación real (varían por proveedor/tier/fecha).
PRICING_PER_MILLION_TOKENS = {
    "openai/gpt-oss-20b": {"prompt": 0.10, "completion": 0.10},
    "gemini-3.6-flash": {"prompt": 0.15, "completion": 0.60},
}

DEFAULT_PRICING = {"prompt": 0.20, "completion": 0.20}


def estimate_cost_usd(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = PRICING_PER_MILLION_TOKENS.get(model_name, DEFAULT_PRICING)
    cost = (prompt_tokens / 1_000_000) * pricing["prompt"] + (completion_tokens / 1_000_000) * pricing["completion"]
    return round(cost, 6)