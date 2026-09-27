"""Run the agent once from the command line and print its trace.

Usage (from the backend/ folder):
    python -m scripts.run_agent "Where is my order 1042?"
    python -m scripts.run_agent "Can I return headphones after 20 days?" --version v2
    python -m scripts.run_agent "Where is my order 1042?" --save     # store in the database
    python -m scripts.run_agent "Where is my order 1042?" --json     # dump the full trace
"""

import argparse
import json


def print_trace(trace):
    print(f"\n{trace.agent_name} {trace.agent_version} ({trace.model}) -> {trace.status}")
    for step in trace.steps:
        tokens = f"  {step.input_tokens} in / {step.output_tokens} out" if step.step_type == "llm" else ""
        print(f"  [{step.step_index}] {step.step_type:4} {step.name:22} {step.latency_ms:6} ms{tokens}")
        if step.step_type == "tool":
            print(f"        args={step.input}  result={json.dumps(step.output)[:100]}")
        if step.error:
            print(f"        ERROR: {step.error}")

    cost = f"${trace.cost_usd:.6f}" if trace.cost_usd is not None else "n/a"
    print(f"\n  total: {trace.latency_ms} ms, {trace.input_tokens + trace.output_tokens} tokens, est. cost {cost}")
    if trace.error_message:
        print(f"  error: {trace.error_message}")
    print(f"\nAnswer:\n{trace.output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--json", action="store_true", help="print the full trace as JSON")
    parser.add_argument("--save", action="store_true", help="save the run and its evaluations to the database")
    parser.add_argument("--no-judge", action="store_true", help="skip the LLM-as-a-judge evaluator")
    args = parser.parse_args()

    if args.save:
        # Imported here so the script still works before a database is set up.
        from services.run_service import run_and_save

        run_id, trace = run_and_save(args.question, args.version, use_judge=not args.no_judge)
        print_trace(trace)
        print(f"\nSaved as run #{run_id}")
        return

    from agent.support_agent import run_agent

    trace = run_agent(args.question, version=args.version)
    if args.json:
        print(json.dumps(trace.to_dict(), indent=2, default=str))
    else:
        print_trace(trace)


if __name__ == "__main__":
    main()
