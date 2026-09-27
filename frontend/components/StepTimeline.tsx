import type { Step } from "@/lib/api";
import { ms, usd } from "@/lib/format";

function Json({ value }: { value: unknown }) {
  return (
    <pre className="mt-1 max-h-64 overflow-auto rounded bg-page p-2 text-xs whitespace-pre-wrap break-words">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function StepBody({ step }: { step: Step }) {
  if (step.step_type === "tool") {
    return (
      <div className="grid gap-2 md:grid-cols-2">
        <div>
          <div className="text-xs text-ink-2">Arguments</div>
          <Json value={step.input} />
        </div>
        <div>
          <div className="text-xs text-ink-2">Tool response</div>
          <Json value={step.output} />
        </div>
      </div>
    );
  }

  const output = step.output as { text?: string; tool_calls?: { name: string; arguments: unknown }[] } | null;
  const messages = (step.input.messages as unknown[]) ?? [];
  return (
    <div className="space-y-2">
      {output?.tool_calls && output.tool_calls.length > 0 && (
        <div className="text-sm">
          Decided to call:{" "}
          {output.tool_calls.map((c, i) => (
            <code key={i} className="mr-2 rounded bg-page px-1">
              {c.name}({JSON.stringify(c.arguments)})
            </code>
          ))}
        </div>
      )}
      {output?.text && <p className="text-sm whitespace-pre-wrap">{output.text}</p>}
      <details>
        <summary className="cursor-pointer text-xs text-ink-2">Prompt sent to the model ({messages.length} messages)</summary>
        <Json value={messages} />
      </details>
    </div>
  );
}

export default function StepTimeline({ steps, totalMs }: { steps: Step[]; totalMs: number }) {
  return (
    <ol className="space-y-3">
      {steps.map((step) => {
        // The bar shows how much of the run's time this step took.
        const share = totalMs > 0 ? Math.max(2, (100 * step.latency_ms) / totalMs) : 0;
        const isLlm = step.step_type === "llm";
        return (
          <li key={step.step_index} className="rounded-lg border border-line bg-surface p-3">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
              <span className="text-muted tabular-nums">{step.step_index + 1}</span>
              <span className="inline-flex items-center gap-1.5 font-medium">
                <span aria-hidden className={`h-2.5 w-2.5 rounded-full ${isLlm ? "bg-series-1" : "bg-series-2"}`} />
                {isLlm ? "LLM" : "Tool"} · {step.name.replaceAll("_", " ")}
              </span>
              <span className="ml-auto text-xs text-ink-2 tabular-nums">
                {ms(step.latency_ms)}
                {step.input_tokens != null && ` · ${step.input_tokens} in / ${step.output_tokens} out tokens · ${usd(step.cost_usd)}`}
              </span>
            </div>
            <div className="mt-2 h-1.5 rounded-full bg-page">
              <div className={`h-1.5 rounded-full ${isLlm ? "bg-series-1" : "bg-series-2"}`} style={{ width: `${share}%` }} />
            </div>
            {step.error && (
              <p className="mt-2 text-sm text-critical">
                <span aria-hidden>✕ </span>
                {step.error}
              </p>
            )}
            <div className="mt-2">
              <StepBody step={step} />
            </div>
          </li>
        );
      })}
    </ol>
  );
}
