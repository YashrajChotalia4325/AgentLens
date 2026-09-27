"""A small "flight recorder" for one agent run.

Usage inside the agent:

    tracer = Tracer("shopwise-support", "v1", "openai/gpt-oss-120b", user_input)
    with tracer.step("tool", "lookup_order", input={"order_id": "1042"}) as step:
        step.output = lookup_order("1042")
    trace = tracer.finish(output="Your order has shipped...")

The tracer only collects data. It doesn't know about the database. That keeps it
easy to test and means we can print a trace, save it, or evaluate it.
"""

import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from tracing.pricing import estimate_cost


def _now():
    return datetime.now(timezone.utc)


@dataclass
class Step:
    step_index: int
    step_type: str  # "llm" or "tool"
    name: str
    input: dict
    output: dict | None = None
    started_at: datetime = field(default_factory=_now)
    latency_ms: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    error: str | None = None

    def record_llm_response(self, model, response):
        self.output = {
            "text": response.text,
            "tool_calls": [{"name": c.name, "arguments": c.arguments} for c in response.tool_calls],
        }
        self.input_tokens = response.input_tokens
        self.output_tokens = response.output_tokens
        self.cost_usd = estimate_cost(model, response.input_tokens, response.output_tokens)
        self.latency_ms = response.latency_ms  # excludes rate-limit waiting


@dataclass
class Trace:
    # Field names match the `runs` table columns on purpose, so evaluators
    # can work with either a fresh Trace or a Run loaded from the database.
    agent_name: str
    agent_version: str
    model: str
    input: str
    output: str
    status: str  # "success", "error" or "max_steps"
    error_message: str | None
    started_at: datetime
    ended_at: datetime
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    steps: list[Step]

    def to_dict(self):
        return asdict(self)


class Tracer:
    def __init__(self, agent_name, agent_version, model, user_input):
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.model = model
        self.user_input = user_input
        self.started_at = _now()
        self.steps = []

    @contextmanager
    def step(self, step_type, name, input):
        step = Step(step_index=len(self.steps), step_type=step_type, name=name, input=input)
        start = time.perf_counter()
        try:
            yield step
        except Exception as e:
            step.error = f"{type(e).__name__}: {e}"
            raise  # record it, but let the caller decide what a crash means
        finally:
            # LLM steps already set their own latency (without retry waits).
            if not step.latency_ms:
                step.latency_ms = int((time.perf_counter() - start) * 1000)
            self.steps.append(step)

    def finish(self, output, status="success", error_message=None):
        llm_steps = [s for s in self.steps if s.step_type == "llm"]
        costs = [s.cost_usd for s in llm_steps if s.cost_usd is not None]
        return Trace(
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            model=self.model,
            input=self.user_input,
            output=output,
            status=status,
            error_message=error_message,
            started_at=self.started_at,
            ended_at=_now(),
            # Sum of step times rather than wall-clock, so rate-limit waits don't count.
            latency_ms=sum(s.latency_ms for s in self.steps),
            input_tokens=sum(s.input_tokens or 0 for s in llm_steps),
            output_tokens=sum(s.output_tokens or 0 for s in llm_steps),
            cost_usd=sum(costs) if costs else None,
            steps=self.steps,
        )
