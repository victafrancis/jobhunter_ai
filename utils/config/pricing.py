# utils/config/pricing.py
PRICES = {
    # prices per 1,000,000 tokens
    "gpt-5":      {"input_per_million": 1.25, "output_per_million": 10.00},
    "gpt-5-mini": {"input_per_million": 0.25, "output_per_million":  2.00},
    "gpt-5-nano": {"input_per_million": 0.05, "output_per_million":  0.40},
}

def compute_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    p = PRICES.get(model)
    if not p:
        return 0.0
    per_in  = p["input_per_million"]  / 1_000_000.0
    per_out = p["output_per_million"] / 1_000_000.0
    return round(prompt_tokens * per_in + completion_tokens * per_out, 6)
