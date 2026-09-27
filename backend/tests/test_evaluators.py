from agent.support_agent import run_agent
from evaluators.efficiency import evaluate_efficiency
from evaluators.faithfulness import evaluate_faithfulness_rules, extract_facts
from evaluators.llm_judge import _parse_judge_reply
from evaluators.task_success import evaluate_task_success

SHIPPED_CASE = {
    "id": "order-status-shipped",
    "input": "Where is my order 1042?",
    "expected": {
        "must_call_tools": ["lookup_order"],
        "must_contain": ["TRK-88213"],
        "must_contain_any": ["shipped", "on its way"],
    },
}


def test_task_success_passes_for_good_agent(fake_llm):
    trace = run_agent("Where is my order 1042?", version="v1")
    result = evaluate_task_success(trace, SHIPPED_CASE)
    assert result["passed"] and result["score"] == 1.0


def test_task_success_fails_for_sloppy_agent(fake_llm):
    trace = run_agent("Where is my order 1042?", version="v2")
    result = evaluate_task_success(trace, SHIPPED_CASE)
    failed = [c["check"] for c in result["details"]["checks"] if not c["passed"]]
    assert not result["passed"]
    assert "called lookup_order" in failed


def test_faithfulness_flags_made_up_numbers(fake_llm):
    good = evaluate_faithfulness_rules(run_agent("Where is my order 1042?", version="v1"))
    bad = evaluate_faithfulness_rules(run_agent("Where is my order 1042?", version="v2"))

    assert good["passed"]
    assert not bad["passed"]
    assert "99.99" in bad["details"]["ungrounded"]


def test_extract_facts_ignores_single_digits():
    assert extract_facts("Delivered in 2 days, cost $34.50, tracking TRK-88213") == ["34.50", "TRK-88213"]


def test_efficiency_uses_test_case_budget(fake_llm):
    trace = run_agent("Where is my order 1042?", version="v1")  # 3 steps
    assert evaluate_efficiency(trace)["passed"]
    assert not evaluate_efficiency(trace, {"budget": {"max_steps": 2}})["passed"]


def test_lookalike_dashes_are_normalized(fake_llm):
    # Real gpt-oss output: "TRK‑88213" with a non-breaking hyphen (U+2011).
    trace = run_agent("Where is my order 1042?", version="v1")
    trace.output = "Order 1042 has shipped. Tracking: TRK‑88213, arriving 2026‑09‑27."

    assert evaluate_task_success(trace, SHIPPED_CASE)["passed"]
    assert "TRK-88213" in evaluate_faithfulness_rules(trace)["details"]["grounded"]


def test_judge_reply_parsing():
    assert _parse_judge_reply('Sure! ```json\n{"score": 4, "reason": "ok"}\n```') == (4, "ok")
