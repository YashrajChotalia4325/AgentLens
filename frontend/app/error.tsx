"use client";

// Shown when a page throws, most often because the backend isn't running.
export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="space-y-3 rounded-lg border border-line bg-surface p-6">
      <h1 className="font-semibold">Couldn&apos;t load this page</h1>
      <p className="text-sm text-ink-2">
        Is the backend running? Start it from the backend folder with <code>uvicorn main:app --reload</code>.
      </p>
      <p className="text-xs text-muted">{error.message}</p>
      <button onClick={reset} className="rounded-md bg-series-1 px-3 py-1 text-sm font-medium text-white">
        Try again
      </button>
    </div>
  );
}
