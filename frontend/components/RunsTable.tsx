import Link from "next/link";

import type { RunSummary } from "@/lib/api";
import { date, ms, num, usd } from "@/lib/format";
import { PassBadge, StatusBadge } from "./ui";

const SHORT_NAMES: Record<string, string> = {
  task_success: "task",
  faithfulness_rules: "facts",
  faithfulness_judge: "judge",
  efficiency: "budget",
};

export default function RunsTable({ runs }: { runs: RunSummary[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="text-xs text-ink-2">
          <tr className="border-b border-line">
            <th className="py-2 pr-3 font-medium">Run</th>
            <th className="py-2 pr-3 font-medium">Input</th>
            <th className="py-2 pr-3 font-medium">Version</th>
            <th className="py-2 pr-3 font-medium">Status</th>
            <th className="py-2 pr-3 text-right font-medium">Latency</th>
            <th className="py-2 pr-3 text-right font-medium">Tokens</th>
            <th className="py-2 pr-3 text-right font-medium">Cost</th>
            <th className="py-2 font-medium">Evaluations</th>
          </tr>
        </thead>
        <tbody className="tabular-nums">
          {runs.map((run) => (
            <tr key={run.id} className="border-b border-line align-top last:border-0">
              <td className="py-2 pr-3">
                <Link href={`/runs/${run.id}`} className="font-medium text-series-1 hover:underline">
                  #{run.id}
                </Link>
                <div className="text-xs text-muted">{date(run.started_at)}</div>
              </td>
              <td className="max-w-xs py-2 pr-3">
                <div className="truncate" title={run.input}>
                  {run.input}
                </div>
                {run.test_case_id && <div className="text-xs text-muted">{run.test_case_id}</div>}
              </td>
              <td className="py-2 pr-3">{run.agent_version}</td>
              <td className="py-2 pr-3">
                <StatusBadge status={run.status} />
              </td>
              <td className="py-2 pr-3 text-right">{ms(run.latency_ms)}</td>
              <td className="py-2 pr-3 text-right">{num(run.total_tokens)}</td>
              <td className="py-2 pr-3 text-right">{usd(run.cost_usd)}</td>
              <td className="py-2">
                <div className="flex flex-wrap gap-1">
                  {Object.entries(run.evaluations).map(([name, result]) => (
                    <PassBadge key={name} passed={result.passed} label={SHORT_NAMES[name] ?? name} />
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
