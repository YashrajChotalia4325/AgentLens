"""The pipeline for one run: agent -> trace -> database -> evaluators -> database."""

from agent.support_agent import run_agent
from database.db import SessionLocal, init_db
from database.save import save_evaluations, save_trace
from evaluators.efficiency import evaluate_efficiency
from evaluators.faithfulness import evaluate_faithfulness_rules
from evaluators.llm_judge import evaluate_with_judge
from evaluators.task_success import evaluate_task_success


def evaluate_run(run, test_case=None, use_judge=True):
    results = [evaluate_efficiency(run, test_case)]

    # Task success needs to know what "correct" means, which only a test case tells us.
    if test_case is not None:
        results.append(evaluate_task_success(run, test_case))

    # Faithfulness of an empty answer from a crashed run means nothing, so skip it.
    if run.status != "error":
        results.append(evaluate_faithfulness_rules(run))
        if use_judge:
            results.append(evaluate_with_judge(run))

    return results


def run_and_save(user_input, version, use_judge=True, experiment_id=None, test_case=None):
    init_db()
    trace = run_agent(user_input, version=version)

    with SessionLocal() as session:
        run = save_trace(
            session,
            trace,
            experiment_id=experiment_id,
            test_case_id=test_case["id"] if test_case else None,
        )
        # We evaluate the saved Run, not the in-memory Trace, so the same code
        # could re-evaluate old runs from the database later.
        save_evaluations(session, run, evaluate_run(run, test_case, use_judge))
        return run.id, trace
