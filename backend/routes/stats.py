from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from database.db import get_session
from database.models import Evaluation, Experiment, Run
from routes.runs import run_summary
from services.regression import compare_experiments, summarize_experiment

router = APIRouter(prefix="/api")


@router.get("/stats")
def get_stats(session=Depends(get_session)):
    # Let the database do the counting and averaging instead of loading every row.
    total_runs, successful_runs, avg_latency, total_cost, avg_cost = session.execute(
        select(
            func.count(Run.id),
            func.count(Run.id).filter(Run.status == "success"),
            func.avg(Run.latency_ms),
            func.sum(Run.cost_usd),
            func.avg(Run.cost_usd),
        )
    ).one()

    avg_eval_score = session.scalar(select(func.avg(Evaluation.score)))
    task_total, task_passed = session.execute(
        select(func.count(Evaluation.id), func.count(Evaluation.id).filter(Evaluation.passed))
        .where(Evaluation.evaluator == "task_success")
    ).one()

    recent_runs = session.scalars(
        select(Run).options(selectinload(Run.steps), selectinload(Run.evaluations)).order_by(Run.id.desc()).limit(10)
    ).all()

    # Trend: one point per experiment, oldest first, so the chart reads left to right.
    experiments = session.scalars(select(Experiment).order_by(Experiment.id.desc()).limit(12)).all()
    trend = [summarize_experiment(session, e.id) for e in reversed(experiments)]

    return {
        "total_runs": total_runs,
        "run_success_rate": 100 * successful_runs / total_runs if total_runs else None,
        "task_success_rate": 100 * task_passed / task_total if task_total else None,
        "avg_latency_ms": avg_latency,
        "total_cost_usd": total_cost,
        "avg_cost_usd": avg_cost,
        "avg_eval_score": avg_eval_score,
        "recent_runs": [run_summary(run) for run in recent_runs],
        "trend": trend,
        "latest_regression": _latest_regression(session, experiments),
    }


def _latest_regression(session, experiments):
    """Compare the newest experiment with the previous one on the same dataset."""
    if not experiments:
        return None
    newest = experiments[0]
    previous = next((e for e in experiments[1:] if e.dataset_name == newest.dataset_name), None)
    if previous is None:
        return None
    report = compare_experiments(session, previous.id, newest.id)
    return {
        "experiment_a": previous.id,
        "experiment_b": newest.id,
        "alerts": report["alerts"],
        "regressed_case_count": len(report["regressed_cases"]),
    }
