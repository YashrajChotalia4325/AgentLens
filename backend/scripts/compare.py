"""Compare two experiments that already exist.

Usage (from the backend/ folder):
    python -m scripts.compare 1 2
"""

import argparse

from database.db import SessionLocal
from scripts.run_experiment import print_comparison
from services.regression import compare_experiments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_a", type=int, help="baseline, e.g. the v1 experiment")
    parser.add_argument("experiment_b", type=int, help="candidate, e.g. the v2 experiment")
    args = parser.parse_args()

    with SessionLocal() as session:
        report = compare_experiments(session, args.experiment_a, args.experiment_b)
    if report is None:
        print("One of those experiments doesn't exist.")
        return
    print_comparison(report)


if __name__ == "__main__":
    main()
