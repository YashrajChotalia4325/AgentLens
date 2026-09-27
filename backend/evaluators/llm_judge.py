"""LLM-as-a-judge: ask a (usually stronger) model to grade the answer.

Rules can only check numbers and keywords. A judge model can read the answer
and notice things like "the policy says 15 days but the agent said 30" or
"the agent said the order was delivered, but the tool said shipped".

Trade-offs to keep in mind:
- it costs tokens and time, so it is optional (--no-judge)
- the judge can be wrong too; that's why we store its reasoning and keep
  the rule-based evaluators next to it
- temperature 0 and a fixed rubric keep its scores reasonably consistent
"""

import json
import re

from config import JUDGE_MODEL
from evaluators.sources import collect_sources
from llm import chat
from tracing.pricing import estimate_cost

JUDGE_PROMPT = """You are grading an answer given by a customer support AI agent.

SOURCES (everything the agent was allowed to know):
{sources}

USER QUESTION:
{question}

AGENT ANSWER:
{answer}

Grade the answer on a 1-5 scale:
5 = every claim is supported by the sources and the question is fully answered
4 = supported by the sources, small omissions
3 = mostly supported, but one claim is unsupported or the answer is incomplete
2 = several unsupported or wrong claims
1 = mostly made up, contradicts the sources, or ignores the question

Saying "I don't know" or asking for missing information (like an order ID) is
correct when the sources don't contain the answer.

Reply with JSON only: {{"score": <1-5>, "reason": "<one or two sentences>"}}"""


def _parse_judge_reply(text):
    # Models sometimes wrap JSON in ```json fences or add text around it,
    # so grab the first {...} block instead of trusting the whole reply.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"judge did not return JSON: {text[:200]}")
    data = json.loads(match.group(0))
    score = int(data["score"])
    if not 1 <= score <= 5:
        raise ValueError(f"judge score out of range: {score}")
    return score, data.get("reason", "")


def evaluate_with_judge(run):
    prompt = JUDGE_PROMPT.format(
        sources="\n".join(collect_sources(run)),
        question=run.input,
        answer=run.output or "(empty answer)",
    )

    try:
        response = chat(JUDGE_MODEL, [{"role": "user", "content": prompt}])
        raw_score, reason = _parse_judge_reply(response.text)
    except Exception as e:
        # A broken judge shouldn't break the run. Record it as a failed evaluation.
        return {
            "evaluator": "faithfulness_judge",
            "score": 0.0,
            "passed": False,
            "details": {"error": f"{type(e).__name__}: {e}"},
        }

    return {
        "evaluator": "faithfulness_judge",
        "score": (raw_score - 1) / 4,  # 1-5 -> 0.0-1.0, same scale as the other evaluators
        "passed": raw_score >= 4,
        "details": {
            "raw_score": raw_score,
            "reason": reason,
            "judge_model": JUDGE_MODEL,
            # Evaluation isn't free either, so we track what the judge cost.
            "judge_tokens": response.input_tokens + response.output_tokens,
            "judge_cost_usd": estimate_cost(JUDGE_MODEL, response.input_tokens, response.output_tokens),
        },
    }
