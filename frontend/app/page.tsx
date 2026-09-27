import Link from "next/link";

import NewRunForm from "@/components/NewRunForm";
import RunsTable from "@/components/RunsTable";
import TrendCharts from "@/components/TrendCharts";
import { AlertList, Card, Empty, StatCard } from "@/components/ui";
import { getStats, getVersions } from "@/lib/api";
import { ms, num, pct, score, usd } from "@/lib/format";

export default async function OverviewPage() {
  const [stats, versions] = await Promise.all([getStats(), getVersions()]);
  const regression = stats.latest_regression;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Overview</h1>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Total runs" value={num(stats.total_runs)} />
        <StatCard label="Run success rate" value={pct(stats.run_success_rate)} note="finished without error" />
        <StatCard label="Task success" value={pct(stats.task_success_rate)} note="test-case runs only" />
        <StatCard label="Avg latency" value={ms(stats.avg_latency_ms)} />
        <StatCard label="Avg cost per run" value={usd(stats.avg_cost_usd)} note={`total ${usd(stats.total_cost_usd)}`} />
        <StatCard label="Avg eval score" value={score(stats.avg_eval_score)} note="0 – 1" />
      </div>

      {regression && (
        <Card title={`Regression check: experiment #${regression.experiment_a} → #${regression.experiment_b}`}>
          <AlertList alerts={regression.alerts} />
          <Link
            href={`/compare?a=${regression.experiment_a}&b=${regression.experiment_b}`}
            className="mt-3 inline-block text-sm text-series-1 hover:underline"
          >
            {regression.regressed_case_count} test case result(s) got worse · see full comparison →
          </Link>
        </Card>
      )}

      <Card title="Evaluation trends">
        {stats.trend.length > 0 ? (
          <TrendCharts experiments={stats.trend} />
        ) : (
          <Empty>
            No experiments yet. Run <code>python -m scripts.run_experiment --version v1</code> in the backend folder.
          </Empty>
        )}
      </Card>

      <Card title="Try the agent">
        <NewRunForm versions={versions} />
      </Card>

      <Card title="Recent runs">
        {stats.recent_runs.length > 0 ? <RunsTable runs={stats.recent_runs} /> : <Empty>No runs recorded yet.</Empty>}
      </Card>
    </div>
  );
}
