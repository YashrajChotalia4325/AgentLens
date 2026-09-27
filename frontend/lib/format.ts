const DASH = "—";

export function ms(value: number | null | undefined) {
  if (value == null) return DASH;
  return value >= 1000 ? `${(value / 1000).toFixed(2)} s` : `${Math.round(value)} ms`;
}

export function usd(value: number | null | undefined) {
  if (value == null) return DASH;
  // Per-run costs are tiny (fractions of a cent), so show enough digits to see differences.
  return value < 0.01 ? `$${value.toFixed(5)}` : `$${value.toFixed(3)}`;
}

export function pct(value: number | null | undefined) {
  return value == null ? DASH : `${value.toFixed(1)}%`;
}

export function score(value: number | null | undefined) {
  return value == null ? DASH : value.toFixed(2);
}

export function num(value: number | null | undefined) {
  return value == null ? DASH : Math.round(value).toLocaleString();
}

export function date(value: string) {
  return new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
