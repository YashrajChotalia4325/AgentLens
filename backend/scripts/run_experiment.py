"""Run the test dataset against an agent version, then print a summary.

Usage (from the backend/ folder):
    python -m scripts.run_experiment --version v1
    python -m scripts.run_experiment --version v2 --compare-to 1
    python -m scripts.run_experiment --version v1 --limit 3 --no-judge   # quick check
"""

import argparse

from database.db import SessionLocal
from services.experiment_service import run_experiment
from services.regression import compare_experiments, summarize_experiment


def fmt(value, pattern="{:.1f}"):
    return "n/a" if value is None else pattern.format(value)


def print_summary(summary):
    print(f"\n#{summary['id']} {summary['name']}  ({summary['run_count']} runs)")
    print(f"  task success : {fmt(summary['task_success_rate'])}%")
    print(f"  eval score   : {fmt(summary['avg_eval_score'], '{:.2f}')}")
    print(f"  avg latency  : {fmt(summary['avg_latency_ms'], '{:.0f}')} ms")
    print(f"  avg tokens   : {fmt(summary['avg_tokens'], '{:.0f}')}")
    print(f"  avg cost     : ${fmt(summary['avg_cost_usd'], '{:.6f}')}/run")
    for evaluator, score in summary["evaluator_scores"].items():
        print(f"    {evaluator:20} {score:.2f}")


def print_comparison(report):
    print_summary(report["a"])
    print_summary(report["b"])
    print("\nAlerts:" if report["alerts"] else "\nNo regressions detected.")
    for alert in report["alerts"]:
        print(f"  ! {alert}")
    for case in report["regressed_cases"]:
        print(f"  worse:  {case['test_case_id']:28} {case['evaluator']:20} run #{case['run_a']} -> #{case['run_b']}")
    for case in report["improved_cases"]:
        print(f"  better: {case['test_case_id']:28} {case['evaluator']:20} run #{case['run_a']} -> #{case['run_b']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--dataset", default="support_v1")
    parser.add_argument("--name", help="a label for this experiment")
    parser.add_argument("--compare-to", type=int, help="experiment ID to compare against")
    parser.add_argument("--limit", type=int, help="only run the first N test cases")
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    experiment_id = run_experiment(
        args.version, args.dataset, name=args.name, use_judge=not args.no_judge, limit=args.limit
    )

    with SessionLocal() as session:
        if args.compare_to:
            print_comparison(compare_experiments(session, args.compare_to, experiment_id))
        else:
            print_summary(summarize_experiment(session, experiment_id))


if __name__ == "__main__":
    main()
