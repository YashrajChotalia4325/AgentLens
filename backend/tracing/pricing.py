"""Estimated prices in USD per 1 million tokens.

These are Groq's published paid-tier prices (checked Sept 2026). On the free
tier you pay nothing, so treat this as "what this run would cost in production".
Update the numbers if prices change or you switch models.
"""

PRICES_PER_MILLION = {
    # model: (input price, output price)
    "openai/gpt-oss-120b": (0.15, 0.60),
    "openai/gpt-oss-20b": (0.075, 0.30),
}


def estimate_cost(model, input_tokens, output_tokens):
    if model not in PRICES_PER_MILLION:
        return None  # unknown model: better to show "no estimate" than a wrong number
    input_price, output_price = PRICES_PER_MILLION[model]
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
