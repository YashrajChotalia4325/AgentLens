"""Efficiency: did the run stay within its budget?

Raw numbers (steps, tokens, latency, cost) are already stored on the run.
This evaluator turns them into a pass/fail by comparing against a budget.
A test case can set its own budget; otherwise we use the defaults below.
"""

DEFAULT_BUDGET = {
    "max_steps": 6,  # LLM calls + tool calls
    "max_tokens": 6000,
    "max_latency_ms": 10000,
}


def evaluate_efficiency(run, test_case=None):
    budget = {**DEFAULT_BUDGET, **((test_case or {}).get("budget", {}))}
    total_tokens = (run.input_tokens or 0) + (run.output_tokens or 0)

    checks = [
        {"check": "steps", "value": len(run.steps), "limit": budget["max_steps"]},
        {"check": "tokens", "value": total_tokens, "limit": budget["max_tokens"]},
        {"check": "latency_ms", "value": run.latency_ms, "limit": budget["max_latency_ms"]},
    ]
    for check in checks:
        check["passed"] = check["value"] <= check["limit"]

    passed_count = sum(c["passed"] for c in checks)
    return {
        "evaluator": "efficiency",
        "score": passed_count / len(checks),
        "passed": passed_count == len(checks),
        "details": {"checks": checks, "cost_usd": run.cost_usd},
    }
