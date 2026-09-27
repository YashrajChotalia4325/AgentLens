import type { EvaluationDetail } from "@/lib/api";
import { score } from "@/lib/format";
import { PassBadge } from "./ui";

const TITLES: Record<string, string> = {
  task_success: "Task success (rules)",
  faithfulness_rules: "Faithfulness (rules)",
  faithfulness_judge: "Faithfulness (LLM judge)",
  efficiency: "Efficiency (budget)",
};

type Check = { check: string; passed: boolean; value?: number; limit?: number };

function Details({ evaluation }: { evaluation: EvaluationDetail }) {
  const d = evaluation.details;

  if (d.error) return <p className="text-sm text-critical">Evaluator error: {String(d.error)}</p>;

  if (Array.isArray(d.checks)) {
    return (
      <ul className="space-y-0.5 text-sm">
        {(d.checks as Check[]).map((c) => (
          <li key={c.check} className="flex gap-2">
            <span aria-hidden className={c.passed ? "text-good-text" : "text-critical"}>
              {c.passed ? "✓" : "✕"}
            </span>
            {c.check}
            {c.limit != null && <span className="text-ink-2">({c.value} / limit {c.limit})</span>}
          </li>
        ))}
      </ul>
    );
  }

  if (evaluation.evaluator === "faithfulness_rules") {
    const grounded = (d.grounded as string[]) ?? [];
    const ungrounded = (d.ungrounded as string[]) ?? [];
    if (d.note) return <p className="text-sm text-ink-2">{String(d.note)}</p>;
    return (
      <div className="space-y-1 text-sm">
        <p>Found in sources: {grounded.length ? grounded.join(", ") : "—"}</p>
        <p className={ungrounded.length ? "text-critical" : ""}>Not found in sources: {ungrounded.length ? ungrounded.join(", ") : "—"}</p>
      </div>
    );
  }

  if (evaluation.evaluator === "faithfulness_judge") {
    return (
      <div className="space-y-1 text-sm">
        <p>
          Judge score {String(d.raw_score)}/5: {String(d.reason)}
        </p>
        <p className="text-xs text-muted">
          judged by {String(d.judge_model)} · {String(d.judge_tokens)} tokens
        </p>
      </div>
    );
  }

  return null;
}

export default function EvaluationList({ evaluations }: { evaluations: EvaluationDetail[] }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {evaluations.map((e) => (
        <div key={e.evaluator} className="rounded-lg border border-line p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-sm font-medium">{TITLES[e.evaluator] ?? e.evaluator}</span>
            <span className="flex items-center gap-2 text-sm tabular-nums">
              {score(e.score)}
              <PassBadge passed={e.passed} />
            </span>
          </div>
          <Details evaluation={e} />
        </div>
      ))}
    </div>
  );
}
