"use client";

// Recharts draws in the browser, so this is a Client Component. The data is
// still fetched on the server and passed in as a prop.
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ExperimentSummary } from "@/lib/api";

const axisProps = {
  tick: { fill: "var(--muted)", fontSize: 12 },
  tickLine: false,
  axisLine: { stroke: "var(--grid)" },
};

const tooltipProps = {
  contentStyle: {
    background: "var(--surface)",
    border: "1px solid var(--line)",
    borderRadius: 8,
    color: "var(--ink)",
    fontSize: 12,
  },
  labelStyle: { color: "var(--ink)", fontWeight: 600 },
};

function endLabel(lastIndex: number, text: string) {
  // Label only the newest point of each line, not every point.
  function EndLabel(props: { x?: number | string; y?: number | string; index?: number }) {
    if (props.index !== lastIndex) return null;
    return (
      <text x={Number(props.x) + 8} y={Number(props.y) + 4} fill="var(--ink-2)" fontSize={12}>
        {text}
      </text>
    );
  }
  return EndLabel;
}

export default function TrendCharts({ experiments }: { experiments: ExperimentSummary[] }) {
  const data = experiments.map((e) => ({
    label: `#${e.id} ${e.agent_version}`,
    taskSuccess: e.task_success_rate == null ? null : Math.round(e.task_success_rate * 10) / 10,
    evalScore: e.avg_eval_score == null ? null : Math.round(e.avg_eval_score * 1000) / 10,
    latency: e.avg_latency_ms == null ? null : Math.round(e.avg_latency_ms),
  }));
  const last = data.length - 1;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <figure>
        <figcaption className="mb-2 text-xs text-ink-2">Quality per experiment (%)</figcaption>
        <div className="h-60">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 96, bottom: 0, left: -16 }}>
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="label" {...axisProps} />
              <YAxis domain={[0, 100]} {...axisProps} />
              <Tooltip {...tooltipProps} formatter={(value) => `${value}%`} />
              <Legend
                iconType="plainline"
                wrapperStyle={{ fontSize: 12 }}
                formatter={(value) => <span style={{ color: "var(--ink-2)" }}>{value}</span>}
              />
              <Line
                name="Task success"
                dataKey="taskSuccess"
                stroke="var(--series-1)"
                strokeWidth={2}
                dot={{ r: 4, fill: "var(--series-1)", stroke: "var(--surface)", strokeWidth: 2 }}
                activeDot={{ r: 6, stroke: "var(--surface)", strokeWidth: 2 }}
                label={endLabel(last, "Task success")}
                isAnimationActive={false}
              />
              <Line
                name="Eval score"
                dataKey="evalScore"
                stroke="var(--series-2)"
                strokeWidth={2}
                dot={{ r: 4, fill: "var(--series-2)", stroke: "var(--surface)", strokeWidth: 2 }}
                activeDot={{ r: 6, stroke: "var(--surface)", strokeWidth: 2 }}
                label={endLabel(last, "Eval score")}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </figure>

      <figure>
        <figcaption className="mb-2 text-xs text-ink-2">Average latency per run (ms)</figcaption>
        <div className="h-60">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="label" {...axisProps} />
              <YAxis {...axisProps} />
              <Tooltip {...tooltipProps} cursor={{ fill: "var(--grid)", opacity: 0.4 }} formatter={(value) => `${value} ms`} />
              <Bar name="Avg latency" dataKey="latency" fill="var(--series-1)" radius={[4, 4, 0, 0]} maxBarSize={24} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </figure>
    </div>
  );
}
