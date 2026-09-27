"""Summarize experiments and compare two of them to find regressions.

Metrics are computed from the stored runs every time instead of being saved
as columns, so they can never go out of date.
"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import Experiment, Run

# How much worse B can be than A before we raise an alert.
THRESHOLDS = {
    "task_success_drop_points": 5.0,  # percentage points
    "eval_score_drop": 0.05,  # on the 0-1 scale
    "latency_increase_pct": 20.0,
    "cost_increase_pct": 20.0,
}


def _average(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _load_runs(session, experiment_id):
    query = (
        select(Run)
        .where(Run.experiment_id == experiment_id)
        .options(selectinload(Run.evaluations), selectinload(Run.steps))
    )
    return session.scalars(query).all()


def _usable_evaluations(run):
    # An evaluator that crashed (e.g. the judge returned bad JSON) says nothing
    # about the agent, so leave it out of the averages.
    return [e for e in run.evaluations if "error" not in (e.details or {})]


def summarize_runs(runs):
    task_results = [e.passed for r in runs for e in _usable_evaluations(r) if e.evaluator == "task_success"]

    scores_by_evaluator = {}
    for run in runs:
        for e in _usable_evaluations(run):
            scores_by_evaluator.setdefault(e.evaluator, []).append(e.score)
    evaluator_averages = {name: _average(scores) for name, scores in scores_by_evaluator.items()}

    costs = [r.cost_usd for r in runs if r.cost_usd is not None]
    return {
        "run_count": len(runs),
        "error_rate": 100 * sum(r.status != "success" for r in runs) / len(runs) if runs else None,
        "task_success_rate": 100 * sum(task_results) / len(task_results) if task_results else None,
        "avg_latency_ms": _average([r.latency_ms for r in runs]),
        "avg_tokens": _average([r.input_tokens + r.output_tokens for r in runs]),
        "avg_steps": _average([len(r.steps) for r in runs]),
        "avg_cost_usd": _average(costs),
        "total_cost_usd": sum(costs) if costs else None,
        # Overall score = mean of the per-evaluator averages, so each evaluator counts equally.
        "avg_eval_score": _average(list(evaluator_averages.values())),
        "evaluator_scores": evaluator_averages,
    }


def summarize_experiment(session, experiment_id):
    experiment = session.get(Experiment, experiment_id)
    if experiment is None:
        return None
    return {
        "id": experiment.id,
        "name": experiment.name,
        "agent_version": experiment.agent_version,
        "dataset_name": experiment.dataset_name,
        "created_at": experiment.created_at,
        **summarize_runs(_load_runs(session, experiment_id)),
    }


def _pct_change(old, new):
    if old in (None, 0) or new is None:
        return None
    return 100 * (new - old) / old


def find_alerts(a, b):
    alerts = []

    if a["task_success_rate"] is not None and b["task_success_rate"] is not None:
        drop = a["task_success_rate"] - b["task_success_rate"]
        if drop >= THRESHOLDS["task_success_drop_points"]:
            alerts.append(f"Performance regression detected: task success decreased by {drop:.1f} percentage points.")

    if a["avg_eval_score"] is not None and b["avg_eval_score"] is not None:
        drop = a["avg_eval_score"] - b["avg_eval_score"]
        if drop >= THRESHOLDS["eval_score_drop"]:
            alerts.append(f"Quality regression: average evaluation score dropped by {drop:.2f}.")

    for evaluator, old_score in a["evaluator_scores"].items():
        new_score = b["evaluator_scores"].get(evaluator)
        if new_score is not None and old_score - new_score >= THRESHOLDS["eval_score_drop"]:
            alerts.append(f"{evaluator} score dropped from {old_score:.2f} to {new_score:.2f}.")

    latency_change = _pct_change(a["avg_latency_ms"], b["avg_latency_ms"])
    if latency_change is not None and latency_change >= THRESHOLDS["latency_increase_pct"]:
        alerts.append(f"Latency regression: average latency increased by {latency_change:.0f}%.")

    cost_change = _pct_change(a["avg_cost_usd"], b["avg_cost_usd"])
    if cost_change is not None and cost_change >= THRESHOLDS["cost_increase_pct"]:
        alerts.append(f"Cost regression: average cost per run increased by {cost_change:.0f}%.")

    if (b["error_rate"] or 0) > (a["error_rate"] or 0):
        alerts.append(f"Error rate increased from {a['error_rate']:.0f}% to {b['error_rate']:.0f}%.")

    return alerts


def _case_results(runs):
    """test_case_id -> {evaluator: passed} for one experiment."""
    results = {}
    for run in runs:
        if run.test_case_id:
            results[run.test_case_id] = {
                "run_id": run.id,
                "passed": {e.evaluator: e.passed for e in _usable_evaluations(run)},
            }
    return results


def compare_experiments(session, experiment_a_id, experiment_b_id):
    a = summarize_experiment(session, experiment_a_id)
    b = summarize_experiment(session, experiment_b_id)
    if a is None or b is None:
        return None

    cases_a = _case_results(_load_runs(session, experiment_a_id))
    cases_b = _case_results(_load_runs(session, experiment_b_id))

    # Averages can hide problems: B might fix 2 cases and break 2 others and
    # look "the same". So we also compare every test case one by one.
    regressed_cases, improved_cases = [], []
    for case_id in sorted(cases_a.keys() & cases_b.keys()):
        for evaluator, passed_in_a in cases_a[case_id]["passed"].items():
            passed_in_b = cases_b[case_id]["passed"].get(evaluator)
            if passed_in_b is None or passed_in_a == passed_in_b:
                continue
            entry = {
                "test_case_id": case_id,
                "evaluator": evaluator,
                "run_a": cases_a[case_id]["run_id"],
                "run_b": cases_b[case_id]["run_id"],
            }
            (regressed_cases if passed_in_a else improved_cases).append(entry)

    return {
        "a": a,
        "b": b,
        "alerts": find_alerts(a, b),
        "regressed_cases": regressed_cases,
        "improved_cases": improved_cases,
    }
