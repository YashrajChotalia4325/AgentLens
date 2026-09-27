// All calls to the FastAPI backend go through here. They run on the Next.js
// server (in Server Components and Server Actions), never in the browser.
import { notFound } from "next/navigation";

export const API_URL = process.env.API_URL ?? "http://localhost:8000";

export type EvalScores = Record<string, { score: number; passed: boolean }>;

export type RunSummary = {
  id: number;
  experiment_id: number | null;
  test_case_id: string | null;
  agent_name: string;
  agent_version: string;
  model: string;
  input: string;
  status: string;
  started_at: string;
  latency_ms: number;
  total_tokens: number;
  cost_usd: number | null;
  step_count: number;
  evaluations: EvalScores;
};

export type Step = {
  step_index: number;
  step_type: "llm" | "tool";
  name: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  latency_ms: number;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: number | null;
  error: string | null;
};

export type EvaluationDetail = {
  evaluator: string;
  score: number;
  passed: boolean;
  details: Record<string, unknown>;
};

export type RunDetail = RunSummary & {
  output: string;
  error_message: string | null;
  input_tokens: number;
  output_tokens: number;
  steps: Step[];
  evaluation_details: EvaluationDetail[];
};

export type ExperimentSummary = {
  id: number;
  name: string;
  agent_version: string;
  dataset_name: string;
  created_at: string;
  run_count: number;
  error_rate: number | null;
  task_success_rate: number | null;
  avg_latency_ms: number | null;
  avg_tokens: number | null;
  avg_steps: number | null;
  avg_cost_usd: number | null;
  total_cost_usd: number | null;
  avg_eval_score: number | null;
  evaluator_scores: Record<string, number>;
};

export type CaseChange = { test_case_id: string; evaluator: string; run_a: number; run_b: number };

export type Comparison = {
  a: ExperimentSummary;
  b: ExperimentSummary;
  alerts: string[];
  regressed_cases: CaseChange[];
  improved_cases: CaseChange[];
};

export type Stats = {
  total_runs: number;
  run_success_rate: number | null;
  task_success_rate: number | null;
  avg_latency_ms: number | null;
  total_cost_usd: number | null;
  avg_cost_usd: number | null;
  avg_eval_score: number | null;
  recent_runs: RunSummary[];
  trend: ExperimentSummary[];
  latest_regression: { experiment_a: number; experiment_b: number; alerts: string[]; regressed_case_count: number } | null;
};

async function get<T>(path: string): Promise<T> {
  // no-store: always ask the API, never reuse an old response.
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (res.status === 404) notFound();
  if (!res.ok) throw new Error(`API ${path} returned ${res.status}`);
  return res.json();
}

export const getStats = () => get<Stats>("/api/stats");
export const getRuns = (experimentId?: string) =>
  get<RunSummary[]>(experimentId ? `/api/runs?limit=200&experiment_id=${experimentId}` : "/api/runs?limit=100");
export const getRun = (id: string) => get<RunDetail>(`/api/runs/${id}`);
export const getExperiments = () => get<ExperimentSummary[]>("/api/experiments");
export const getComparison = (a: string, b: string) => get<Comparison>(`/api/experiments/compare?a=${a}&b=${b}`);
export const getVersions = () => get<{ version: string; model: string }[]>("/api/versions");
