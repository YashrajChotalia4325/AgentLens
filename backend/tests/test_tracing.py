import pytest

from agent.support_agent import run_agent
from tracing.pricing import estimate_cost
from tracing.tracer import Tracer


def test_step_records_error_and_still_saves_the_step():
    tracer = Tracer("test-agent", "v0", "some-model", "hi")
    with pytest.raises(ValueError):
        with tracer.step("tool", "broken_tool", input={}):
            raise ValueError("boom")

    assert len(tracer.steps) == 1
    assert tracer.steps[0].error == "ValueError: boom"


def test_cost_estimate_for_known_and_unknown_models():
    assert estimate_cost("openai/gpt-oss-120b", 1_000_000, 0) == pytest.approx(0.15)
    assert estimate_cost("mystery-model", 100, 100) is None


def test_agent_run_produces_full_trace(fake_llm):
    trace = run_agent("Where is my order 1042?", version="v1")

    assert trace.status == "success"
    assert [s.name for s in trace.steps] == ["planner", "lookup_order", "final_answer"]
    assert trace.steps[1].input == {"order_id": "1042"}
    assert trace.steps[1].output["tracking_number"] == "TRK-88213"
    assert trace.input_tokens == 500 + 600
    assert trace.cost_usd > 0
    assert "TRK-88213" in trace.output


def test_llm_snapshot_is_not_changed_by_later_steps(fake_llm):
    trace = run_agent("Where is my order 1042?", version="v1")
    # The planner saw only the system + user message, even though the
    # conversation grew afterwards.
    assert len(trace.steps[0].input["messages"]) == 2


def test_crash_is_recorded_as_error_run(monkeypatch):
    import agent.support_agent

    def broken_chat(*args, **kwargs):
        raise ConnectionError("network down")

    monkeypatch.setattr(agent.support_agent, "chat", broken_chat)
    trace = run_agent("Where is my order 1042?")

    assert trace.status == "error"
    assert "network down" in trace.error_message
    assert trace.steps[0].error is not None
