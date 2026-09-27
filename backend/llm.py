"""The only file that talks to the LLM provider.

Groq exposes an OpenAI-compatible API, so we use the `openai` package with a
different base_url. Switching to another OpenAI-compatible provider (Gemini,
OpenRouter, a local server) only means changing LLM_BASE_URL and the model name.
"""

import json
import time
from dataclasses import dataclass, field

from openai import OpenAI, RateLimitError

from config import LLM_API_KEY, LLM_BASE_URL

MAX_RATE_LIMIT_RETRIES = 5

_client = None


def get_client():
    global _client
    if _client is None:
        if not LLM_API_KEY:
            raise RuntimeError("LLM_API_KEY is not set. Copy backend/.env.example to backend/.env and add your key.")
        # We do our own retries (see chat()), so turn off the SDK's hidden ones.
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, max_retries=0)
    return _client


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    assistant_message: dict = field(default_factory=dict)  # to append back into the conversation
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0  # time of the successful request only, without rate-limit waits


def _create_with_retries(kwargs):
    # Groq's free tier allows ~8K tokens/minute, so running a dataset hits 429 errors.
    # We wait and retry, but only time the attempt that succeeded. Otherwise the
    # trace would say "the model took 40 seconds" when really we were waiting in line.
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        start = time.perf_counter()
        try:
            response = get_client().chat.completions.create(**kwargs)
            return response, int((time.perf_counter() - start) * 1000)
        except RateLimitError as e:
            if attempt == MAX_RATE_LIMIT_RETRIES:
                raise
            wait = float(e.response.headers.get("retry-after", 2 ** attempt))
            print(f"  rate limited, waiting {wait:.0f}s...")
            time.sleep(min(wait, 60))


def chat(model, messages, tools=None, temperature=0.0):
    kwargs = {"model": model, "messages": messages, "temperature": temperature}
    if tools:
        kwargs["tools"] = tools

    response, latency_ms = _create_with_retries(kwargs)
    message = response.choices[0].message

    tool_calls = []
    for call in message.tool_calls or []:
        try:
            arguments = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            # Models occasionally produce broken JSON. Pass it on so the tool can report the error.
            arguments = {"_raw": call.function.arguments}
        tool_calls.append(ToolCall(id=call.id, name=call.function.name, arguments=arguments))

    # Build the assistant message by hand instead of dumping the SDK object,
    # so provider-specific extra fields (like reasoning text) don't get sent back.
    assistant_message = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in message.tool_calls
        ]

    usage = response.usage
    return LLMResponse(
        text=message.content or "",
        tool_calls=tool_calls,
        assistant_message=assistant_message,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
        latency_ms=latency_ms,
    )
