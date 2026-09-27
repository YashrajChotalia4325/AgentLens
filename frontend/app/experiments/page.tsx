import Link from "next/link";

import CompareForm from "@/components/CompareForm";
import { Card, Empty } from "@/components/ui";
import { getExperiments } from "@/lib/api";
import { date, ms, num, pct, score, usd } from "@/lib/format";

export default async function ExperimentsPage() {
  const experiments = await getExperiments();

  if (experiments.length === 0) {
    return (
      <Empty>
        No experiments yet. From the backend folder run <code>python -m scripts.run_experiment --version v1</code>, then again
        with <code>--version v2</code>.
      </Empty>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Experiments</h1>

      {experiments.length >= 2 && (
        <Card title="Compare two experiments">
          <CompareForm experiments={experiments} />
        </Card>
      )}

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="text-xs text-ink-2">
              <tr className="border-b border-line">
                <th className="py-2 pr-3 font-medium">Experiment</th>
                <th className="py-2 pr-3 font-medium">Version</th>
                <th className="py-2 pr-3 text-right font-medium">Runs</th>
                <th className="py-2 pr-3 text-right font-medium">Task success</th>
                <th className="py-2 pr-3 text-right font-medium">Eval score</th>
                <th className="py-2 pr-3 text-right font-medium">Avg latency</th>
                <th className="py-2 pr-3 text-right font-medium">Avg tokens</th>
                <th className="py-2 text-right font-medium">Avg cost</th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {experiments.map((e) => (
                <tr key={e.id} className="border-b border-line last:border-0">
                  <td className="py-2 pr-3">
                    <Link href={`/runs?experiment_id=${e.id}`} className="font-medium text-series-1 hover:underline">
                      #{e.id} {e.name}
                    </Link>
                    <div className="text-xs text-muted">
                      {e.dataset_name} · {date(e.created_at)}
                    </div>
                  </td>
                  <td className="py-2 pr-3">{e.agent_version}</td>
                  <td className="py-2 pr-3 text-right">{e.run_count}</td>
                  <td className="py-2 pr-3 text-right">{pct(e.task_success_rate)}</td>
                  <td className="py-2 pr-3 text-right">{score(e.avg_eval_score)}</td>
                  <td className="py-2 pr-3 text-right">{ms(e.avg_latency_ms)}</td>
                  <td className="py-2 pr-3 text-right">{num(e.avg_tokens)}</td>
                  <td className="py-2 text-right">{usd(e.avg_cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
