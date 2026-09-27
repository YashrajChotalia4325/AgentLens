"""Rule-based task success: did the agent do what this test case expects?

A test case describes what a good run looks like, for example:

    "expected": {
        "must_call_tools": ["lookup_order"],
        "must_not_call_tools": [],
        "must_contain": ["TRK-88213"],
        "must_contain_any": ["shipped", "on its way", "in transit"],
        "must_not_contain": ["delivered"]
    }

Each rule becomes one check. Score = checks passed / total checks.
The run only counts as a success if every check passes.
"""

from evaluators.sources import normalize_text


def evaluate_task_success(run, test_case):
    expected = test_case.get("expected", {})
    answer = normalize_text(run.output).lower()
    tools_called = {s.name for s in run.steps if s.step_type == "tool"}

    checks = [{"check": "run completed", "passed": run.status == "success"}]

    for tool in expected.get("must_call_tools", []):
        checks.append({"check": f"called {tool}", "passed": tool in tools_called})

    for tool in expected.get("must_not_call_tools", []):
        checks.append({"check": f"did not call {tool}", "passed": tool not in tools_called})

    for text in expected.get("must_contain", []):
        checks.append({"check": f"answer mentions '{text}'", "passed": text.lower() in answer})

    options = expected.get("must_contain_any", [])
    if options:
        found = any(option.lower() in answer for option in options)
        checks.append({"check": f"answer mentions one of {options}", "passed": found})

    for text in expected.get("must_not_contain", []):
        checks.append({"check": f"answer does not mention '{text}'", "passed": text.lower() not in answer})

    passed_count = sum(c["passed"] for c in checks)
    return {
        "evaluator": "task_success",
        "score": passed_count / len(checks),
        "passed": passed_count == len(checks),
        "details": {"checks": checks},
    }
