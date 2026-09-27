"""Rule-based faithfulness: are the facts in the answer backed by the sources?

We can't understand free text with rules, but we can check the facts that
matter most in a support answer: numbers, prices, dates, order IDs and
tracking numbers. If the answer says "$79.99" and no tool ever returned
79.99, the agent probably made it up.

Limitations (this is why we also have an LLM judge):
- it can't catch a wrong claim without a number ("your order was delivered")
- "September 27" vs "2026-09-27" is only matched through the "27"
"""

import re

from evaluators.sources import collect_sources, normalize_text

PASS_THRESHOLD = 0.75

TRACKING_PATTERN = re.compile(r"\bTRK-\d+\b", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")


def extract_facts(answer):
    answer = normalize_text(answer).replace(",", "")  # "1,000" -> "1000"
    facts = set(TRACKING_PATTERN.findall(answer))
    for number in NUMBER_PATTERN.findall(TRACKING_PATTERN.sub("", answer)):
        # Single digits like "1" or "2" are too common to prove anything.
        if len(number) >= 2 or "." in number:
            facts.add(number)
    return sorted(facts)


def _number_variants(fact):
    # Tool results are JSON, where 34.50 is written as 34.5 and 15.00 as 15.0,
    # so "$34.50" or "$15" in the answer should still match.
    variants = {fact}
    if "." in fact:
        variants.add(fact.rstrip("0").rstrip("."))
    else:
        variants.add(fact + ".0")
    return variants


def evaluate_faithfulness_rules(run):
    facts = extract_facts(run.output or "")
    source_text = normalize_text(" ".join(collect_sources(run))).lower().replace(",", "")

    if not facts:
        return {
            "evaluator": "faithfulness_rules",
            "score": 1.0,
            "passed": True,
            "details": {"note": "no checkable facts (numbers, IDs) in the answer", "facts": []},
        }

    grounded, ungrounded = [], []
    for fact in facts:
        if any(v.lower() in source_text for v in _number_variants(fact)):
            grounded.append(fact)
        else:
            ungrounded.append(fact)

    score = len(grounded) / len(facts)
    return {
        "evaluator": "faithfulness_rules",
        "score": score,
        "passed": score >= PASS_THRESHOLD,
        "details": {"grounded": grounded, "ungrounded": ungrounded},
    }
