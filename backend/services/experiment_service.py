"""Run a whole test dataset against one agent version."""

import json
import time
from pathlib import Path

from database.db import SessionLocal, init_db
from database.models import Experiment
from services.run_service import run_and_save

DATASETS_DIR = Path(__file__).parent.parent / "datasets"

# A short pause between test cases keeps us under Groq's free-tier limits.
PAUSE_BETWEEN_CASES_SECONDS = 2


def load_dataset(dataset_name):
    with open(DATASETS_DIR / f"{dataset_name}.json", encoding="utf-8") as f:
        return json.load(f)


def run_experiment(version, dataset_name, name=None, use_judge=True, limit=None):
    init_db()
    test_cases = load_dataset(dataset_name)[:limit]

    with SessionLocal() as session:
        experiment = Experiment(
            name=name or f"{version} on {dataset_name}",
            agent_version=version,
            dataset_name=dataset_name,
        )
        session.add(experiment)
        session.commit()
        experiment_id = experiment.id

    print(f"Experiment #{experiment_id}: {len(test_cases)} test cases, agent {version}")
    for i, test_case in enumerate(test_cases, start=1):
        run_id, trace = run_and_save(
            test_case["input"], version, use_judge=use_judge, experiment_id=experiment_id, test_case=test_case
        )
        print(f"  [{i}/{len(test_cases)}] {test_case['id']:28} run #{run_id}  {trace.status}  {trace.latency_ms} ms")
        time.sleep(PAUSE_BETWEEN_CASES_SECONDS)

    return experiment_id
