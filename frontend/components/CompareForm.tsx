import type { ExperimentSummary } from "@/lib/api";

// A plain GET form: submitting it just navigates to /compare?a=..&b=..
// so no JavaScript is needed.
export default function CompareForm({ experiments, a, b }: { experiments: ExperimentSummary[]; a?: string; b?: string }) {
  const options = experiments.map((e) => (
    <option key={e.id} value={e.id}>
      #{e.id} · {e.name}
    </option>
  ));
  return (
    <form action="/compare" className="flex flex-wrap items-center gap-2 text-sm">
      <label className="text-ink-2">Baseline</label>
      <select name="a" defaultValue={a ?? experiments[1]?.id} className="rounded-md border border-line bg-page px-2 py-1">
        {options}
      </select>
      <label className="text-ink-2">vs candidate</label>
      <select name="b" defaultValue={b ?? experiments[0]?.id} className="rounded-md border border-line bg-page px-2 py-1">
        {options}
      </select>
      <button type="submit" className="rounded-md bg-series-1 px-3 py-1 font-medium text-white">
        Compare
      </button>
    </form>
  );
}
