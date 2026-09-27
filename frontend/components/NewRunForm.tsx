"use client";

import { useActionState } from "react";

import { createRun, type NewRunState } from "@/app/actions";

export default function NewRunForm({ versions }: { versions: { version: string; model: string }[] }) {
  const [state, formAction, pending] = useActionState<NewRunState, FormData>(createRun, { error: null });

  return (
    <form action={formAction} className="space-y-3">
      <textarea
        name="input"
        rows={2}
        required
        placeholder="e.g. Can I return the headphones from order 1041?"
        className="w-full rounded-md border border-line bg-page p-2 text-sm"
      />
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <select name="version" className="rounded-md border border-line bg-page px-2 py-1">
          {versions.map((v) => (
            <option key={v.version} value={v.version}>
              {v.version} ({v.model})
            </option>
          ))}
        </select>
        <label className="flex items-center gap-1 text-ink-2">
          <input type="checkbox" name="use_judge" defaultChecked /> LLM judge
        </label>
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-series-1 px-3 py-1 font-medium text-white disabled:opacity-60"
        >
          {pending ? "Running agent…" : "Run agent"}
        </button>
      </div>
      {state.error && <p className="text-sm text-critical">{state.error}</p>}
    </form>
  );
}
