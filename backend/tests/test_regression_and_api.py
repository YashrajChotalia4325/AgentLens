"""End-to-end: run two experiments with the fake LLM, store them, compare them, read them over HTTP."""

from fastapi.testclient import TestClient

from database.db import SessionLocal
from main import app
from services.experiment_service import run_experiment
from services.regression import compare_experiments


def test_v2_regression_is_detected_and_served_by_api(fake_llm):
    exp_v1 = run_experiment("v1", "support_v1", limit=2)
    exp_v2 = run_experiment("v2", "support_v1", limit=2)

    with SessionLocal() as session:
        report = compare_experiments(session, exp_v1, exp_v2)

    assert report["a"]["task_success_rate"] == 100.0
    assert report["b"]["task_success_rate"] == 0.0
    assert any("task success decreased by 100.0" in alert for alert in report["alerts"])
    regressed = {(c["test_case_id"], c["evaluator"]) for c in report["regressed_cases"]}
    assert ("order-status-shipped", "task_success") in regressed

    with TestClient(app) as client:
        stats = client.get("/api/stats").json()
        assert stats["total_runs"] >= 4
        assert stats["latest_regression"]["alerts"]

        run_id = client.get(f"/api/runs?experiment_id={exp_v1}").json()[-1]["id"]  # first case: order 1042
        run = client.get(f"/api/runs/{run_id}").json()
        assert [s["step_type"] for s in run["steps"]] == ["llm", "tool", "llm"]
        assert {e["evaluator"] for e in run["evaluation_details"]} == {
            "efficiency", "task_success", "faithfulness_rules", "faithfulness_judge"
        }

        compare = client.get(f"/api/experiments/compare?a={exp_v1}&b={exp_v2}").json()
        assert compare["alerts"] == report["alerts"]
        assert client.get("/api/runs/999999").status_code == 404
