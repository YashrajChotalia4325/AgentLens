// Small presentational pieces shared by several pages.

export function Card({ title, children, className = "" }: { title?: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-line bg-surface p-4 ${className}`}>
      {title && <h2 className="mb-3 text-sm font-semibold text-ink-2">{title}</h2>}
      {children}
    </section>
  );
}

export function StatCard({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <div className="text-xs text-ink-2">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
      {note && <div className="mt-1 text-xs text-muted">{note}</div>}
    </div>
  );
}

// Pass/fail is never shown by color alone: there's always an icon and a word.
export function PassBadge({ passed, label }: { passed: boolean; label?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${
        passed ? "border-good text-good-text" : "border-critical text-critical"
      }`}
    >
      <span aria-hidden>{passed ? "✓" : "✕"}</span>
      {label ?? (passed ? "pass" : "fail")}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return <PassBadge passed={status === "success"} label={status} />;
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <p className="rounded-lg border border-dashed border-line p-6 text-center text-sm text-ink-2">{children}</p>;
}

export function AlertList({ alerts }: { alerts: string[] }) {
  if (alerts.length === 0) {
    return (
      <p className="text-sm text-good-text">
        <span aria-hidden>✓ </span>No regressions detected.
      </p>
    );
  }
  return (
    <ul className="space-y-1">
      {alerts.map((alert) => (
        <li key={alert} className="flex gap-2 text-sm">
          <span aria-hidden className="text-critical">
            ▲
          </span>
          <span>{alert}</span>
        </li>
      ))}
    </ul>
  );
}
