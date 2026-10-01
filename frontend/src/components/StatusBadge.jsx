const NEUTRAL_MAP = {
  NOT_FLAGGED: "badge-neutral",
  FLAGGED: "badge-medium",
  INVESTIGATED: "badge-accent",
  SUBMITTED: "badge-neutral",
  UNDER_REVIEW: "badge-medium",
  CLOSED: "badge-low",
  OPEN: "badge-medium",
  IN_PROGRESS: "badge-accent",
};

export default function StatusBadge({ value }) {
  if (!value) return <span className="badge badge-neutral">—</span>;
  const cls = NEUTRAL_MAP[value] || "badge-neutral";
  return <span className={`badge ${cls}`}>{value.replaceAll("_", " ")}</span>;
}
