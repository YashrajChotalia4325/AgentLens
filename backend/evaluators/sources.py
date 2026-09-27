import json

# Models often write "TRK‑88213" or "5–7 days" with look-alike Unicode dashes
# (non-breaking hyphen, en dash...) and non-breaking spaces. To a person they
# look identical, but "TRK-88213" in "TRK‑88213" is False in Python. So every
# rule-based evaluator compares normalized text.
LOOKALIKES = str.maketrans({
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
    " ": " ", " ": " ",
})


def normalize_text(text):
    return (text or "").translate(LOOKALIKES)


def collect_sources(run):
    """Everything the agent was allowed to know when it answered.

    That's the system prompt and user message (from the first LLM call) plus
    every tool result. A grounded answer should only state facts from here.
    """
    sources = []
    llm_steps = [s for s in run.steps if s.step_type == "llm"]
    if llm_steps:
        for message in llm_steps[0].input.get("messages", []):
            sources.append(f"[{message['role']}] {message.get('content', '')}")
    else:
        sources.append(f"[user] {run.input}")

    for step in run.steps:
        if step.step_type == "tool":
            sources.append(f"[tool {step.name}] {json.dumps(step.output)}")
    return sources
