"""Agent versions.

A "version" is everything that can change the agent's behaviour: the model,
the system prompt and the step limit. Later, AgentLens runs the same test
dataset against two versions and compares them.

v1: bigger model, detailed instructions.
v2: smaller/cheaper model, shorter prompt. Faster and cheaper, but is it as good?
"""

V1_PROMPT = """You are the customer support assistant for ShopWise, an online store.

Rules:
- Always use lookup_order to get order details. Never guess order status, dates or prices.
- Always use search_knowledge_base before answering questions about policies (returns, refunds, shipping, warranty, payments, cancellations).
- Use calculator for any arithmetic, such as totals or refund amounts.
- Only state facts that come from tool results. If the information is not available, say so.
- If the user asks about an order but gives no order ID, ask for it.
- Keep answers short and friendly (2-4 sentences). Include the order ID when talking about an order.

Today's date is {today}."""

V2_PROMPT = """You are a helpful support assistant for ShopWise. Answer the customer briefly. Today's date is {today}."""

VERSIONS = {
    "v1": {
        "agent_name": "shopwise-support",
        "model": "openai/gpt-oss-120b",
        "system_prompt": V1_PROMPT,
        "max_steps": 6,
    },
    "v2": {
        "agent_name": "shopwise-support",
        "model": "openai/gpt-oss-20b",
        "system_prompt": V2_PROMPT,
        "max_steps": 4,
    },
}


def get_version(version):
    if version not in VERSIONS:
        raise ValueError(f"Unknown agent version '{version}'. Choose from: {', '.join(VERSIONS)}")
    return VERSIONS[version]
