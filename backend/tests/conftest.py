"""Test setup.

Tests must not call the real LLM (slow, rate-limited, non-deterministic) or need
a Postgres server. So we:
  - point DATABASE_URL at a throwaway SQLite file before anything imports db.py
  - replace llm.chat with a scripted fake that behaves like a good or bad agent
"""

import json
import os
import re
import tempfile

TEST_DB = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

import pytest  # noqa: E402

from llm import LLMResponse, ToolCall  # noqa: E402


def fake_chat(model, messages, tools=None, temperature=0.0):
    """Pretend LLM.

    - the judge (no tools) always returns score 5
    - gpt-oss-120b acts like a careful agent: looks up the order, then answers from it
    - gpt-oss-20b acts like a sloppy agent: answers immediately and makes things up
    """
    if tools is None:
        return LLMResponse(text='```json\n{"score": 5, "reason": "Supported by the tool output."}\n```',
                           input_tokens=300, output_tokens=20, latency_ms=5)

    last = messages[-1]
    if model == "openai/gpt-oss-20b":
        return LLMResponse(text="Your order was delivered yesterday for $99.99.", input_tokens=200,
                           output_tokens=15, latency_ms=5, assistant_message={"role": "assistant", "content": "..."})

    if last["role"] == "user":
        order_id = re.search(r"\d{4}", last["content"]).group(0)
        call = ToolCall(id="call_1", name="lookup_order", arguments={"order_id": order_id})
        return LLMResponse(text="", tool_calls=[call], input_tokens=500, output_tokens=30, latency_ms=5,
                           assistant_message={"role": "assistant", "content": ""})

    order = json.loads(last["content"])
    text = f"Order {order['order_id']} is {order['status']}."
    if "tracking_number" in order:
        text += f" Tracking number: {order['tracking_number']}."
    return LLMResponse(text=text, input_tokens=600, output_tokens=25, latency_ms=5,
                       assistant_message={"role": "assistant", "content": text})


@pytest.fixture
def fake_llm(monkeypatch):
    import agent.support_agent
    import evaluators.llm_judge
    import services.experiment_service

    monkeypatch.setattr(agent.support_agent, "chat", fake_chat)
    monkeypatch.setattr(evaluators.llm_judge, "chat", fake_chat)
    monkeypatch.setattr(services.experiment_service, "PAUSE_BETWEEN_CASES_SECONDS", 0)
