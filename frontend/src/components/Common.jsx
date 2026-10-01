import { Inbox, AlertTriangle, AlertCircle, Info } from "lucide-react";

export function Loader({ label = "Loading…" }) {
  return (
    <div className="loader-wrap">
      <span className="spinner" />
      {label}
    </div>
  );
}

export function EmptyState({ title = "Nothing here yet", hint }) {
  return (
    <div className="empty-state">
      <Inbox />
      <div className="empty-state__title">{title}</div>
      {hint && <div>{hint}</div>}
    </div>
  );
}

export function Banner({ type = "info", children }) {
  const Icon = type === "error" ? AlertCircle : type === "warning" ? AlertTriangle : Info;
  return (
    <div className={`banner banner-${type}`}>
      <Icon />
      <div>{children}</div>
    </div>
  );
}

export function formatCurrency(value) {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
