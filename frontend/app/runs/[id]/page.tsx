import Link from "next/link";

import EvaluationList from "@/components/EvaluationList";
import StepTimeline from "@/components/StepTimeline";
import { Card, Empty, StatCard, StatusBadge } from "@/components/ui";
import { getRun } from "@/lib/api";
import { date, ms, num, usd } from "@/lib/format";

export default async function RunDetailPage(props: PageProps<"/runs/[id]">) {
  const { id } = await props.params;
  const run = await getRun(id);

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-semibold">Run #{run.id}</h1>
          <StatusBadge status={run.status} />
        </div>
        <p className="mt-1 text-sm text-ink-2">
          {run.agent_name} {run.agent_version} · {run.model} · {date(run.started_at)}
          {run.experiment_id && (
            <>
              {" · "}
              <Link href={`/runs?experiment_id=${run.experiment_id}`} className="text-series-1 hover:underline">
                experiment #{run.experiment_id}
              </Link>
              {run.test_case_id && ` / ${run.test_case_id}`}
            </>
          )}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Latency" value={ms(run.latency_ms)} note="model + tool time" />
        <StatCard label="Steps" value={num(run.steps.length)} />
        <StatCard label="Tokens" value={num(run.input_tokens + run.output_tokens)} note={`${num(run.input_tokens)} in / ${num(run.output_tokens)} out`} />
        <StatCard label="Estimated cost" value={usd(run.cost_usd)} />
      </div>

      <Card title="User input">
        <p className="text-sm whitespace-pre-wrap">{run.input}</p>
      </Card>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-ink-2">Steps</h2>
        {run.steps.length > 0 ? <StepTimeline steps={run.steps} totalMs={run.latency_ms} /> : <Empty>No steps recorded.</Empty>}
      </div>

      <Card title="Final answer">
        {run.error_message && <p className="mb-2 text-sm text-critical">{run.error_message}</p>}
        <p className="text-sm whitespace-pre-wrap">{run.output || "(no answer)"}</p>
      </Card>

      <Card title="Evaluations">
        {run.evaluation_details.length > 0 ? (
          <EvaluationList evaluations={run.evaluation_details} />
        ) : (
          <Empty>This run has no evaluations.</Empty>
        )}
      </Card>
    </div>
  );
}
