import Link from "next/link";

import CompareForm from "@/components/CompareForm";
import { AlertList, Card, Empty } from "@/components/ui";
import { getComparison, getExperiments, type CaseChange, type ExperimentSummary } from "@/lib/api";
import { ms, num, pct, score, usd } from "@/lib/format";

type Metric = {
  label: string;
  key: keyof ExperimentSummary;
  format: (v: number | null) => string;
  higherIsBetter: boolean;
  isRate?: boolean;
};

const METRICS: Metric[] = [
  { label: "Task success", key: "task_success_rate", format: pct, higherIsBetter: true, isRate: true },
  { label: "Avg eval score", key: "avg_eval_score", format: score, higherIsBetter: true },
  { label: "Failed runs", key: "error_rate", format: pct, higherIsBetter: false, isRate: true },
  { label: "Avg latency", key: "avg_latency_ms", format: ms, higherIsBetter: false },
  { label: "Avg tokens", key: "avg_tokens", format: num, higherIsBetter: false },
  { label: "Avg steps", key: "avg_steps", format: (v) => (v == null ? "—" : v.toFixed(1)), higherIsBetter: false },
  { label: "Avg cost per run", key: "avg_cost_usd", format: usd, higherIsBetter: false },
];

function Change({ a, b, metric }: { a: number | null; b: number | null; metric: Metric }) {
  if (a == null || b == null || a === b) return <span className="text-muted">no change</span>;
  const better = metric.higherIsBetter ? b > a : b < a;
  // For rates, "86% -> 79%" is a change of 7 points. Saying "-8%" would be confusing.
  let amount = "";
  if (metric.isRate) amount = `${Math.abs(b - a).toFixed(1)} pts`;
  else if (a !== 0) amount = `${Math.abs(((b - a) / a) * 100).toFixed(0)}%`;
  return (
    <span className={better ? "text-good-text" : "text-critical"}>
      <span aria-hidden>{b > a ? "▲" : "▼"} </span>
      {amount} {better ? "better" : "worse"}
    </span>
  );
}

function CaseTable({ cases }: { cases: CaseChange[] }) {
  return (
    <ul className="space-y-1 text-sm">
      {cases.map((c) => (
        <li key={`${c.test_case_id}-${c.evaluator}`} className="flex flex-wrap gap-x-3">
          <span className="font-medium">{c.test_case_id}</span>
          <span className="text-ink-2">{c.evaluator}</span>
          <span>
            <Link href={`/runs/${c.run_a}`} className="text-series-1 hover:underline">
              run #{c.run_a}
            </Link>
            {" → "}
            <Link href={`/runs/${c.run_b}`} className="text-series-1 hover:underline">
              run #{c.run_b}
            </Link>
          </span>
        </li>
      ))}
    </ul>
  );
}

export default async function ComparePage(props: PageProps<"/compare">) {
  const { a, b } = await props.searchParams;
  const experiments = await getExperiments();

  if (experiments.length < 2) {
    return <Empty>You need at least two experiments to compare. Run the dataset with v1 and with v2 first.</Empty>;
  }
  if (typeof a !== "string" || typeof b !== "string") {
    return (
      <div className="space-y-4">
        <h1 className="text-xl font-semibold">Compare experiments</h1>
        <Card>
          <CompareForm experiments={experiments} />
        </Card>
      </div>
    );
  }

  const report = await getComparison(a, b);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Compare experiments</h1>
      <Card>
        <CompareForm experiments={experiments} a={a} b={b} />
      </Card>

      <Card title="Alerts">
        <AlertList alerts={report.alerts} />
      </Card>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="text-xs text-ink-2">
              <tr className="border-b border-line">
                <th className="py-2 pr-3 font-medium">Metric</th>
                <th className="py-2 pr-3 text-right font-medium">
                  #{report.a.id} {report.a.agent_version} (baseline)
                </th>
                <th className="py-2 pr-3 text-right font-medium">
                  #{report.b.id} {report.b.agent_version} (candidate)
                </th>
                <th className="py-2 font-medium">Change</th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {METRICS.map((m) => {
                const valueA = report.a[m.key] as number | null;
                const valueB = report.b[m.key] as number | null;
                return (
                  <tr key={m.key} className="border-b border-line last:border-0">
                    <td className="py-2 pr-3">{m.label}</td>
                    <td className="py-2 pr-3 text-right">{m.format(valueA)}</td>
                    <td className="py-2 pr-3 text-right">{m.format(valueB)}</td>
                    <td className="py-2">
                      <Change a={valueA} b={valueB} metric={m} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card title={`Got worse (${report.regressed_cases.length})`}>
          {report.regressed_cases.length > 0 ? <CaseTable cases={report.regressed_cases} /> : <p className="text-sm text-ink-2">None.</p>}
        </Card>
        <Card title={`Got better (${report.improved_cases.length})`}>
          {report.improved_cases.length > 0 ? <CaseTable cases={report.improved_cases} /> : <p className="text-sm text-ink-2">None.</p>}
        </Card>
      </div>
    </div>
  );
}
