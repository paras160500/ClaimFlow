import { ShieldCheck, ShieldAlert, ShieldX, ShieldQuestion } from "lucide-react";

const CONFIG = {
  LOW: { cls: "badge-low", Icon: ShieldCheck, label: "Low risk" },
  MEDIUM: { cls: "badge-medium", Icon: ShieldAlert, label: "Medium risk" },
  HIGH: { cls: "badge-high", Icon: ShieldX, label: "High risk" },
  UNKNOWN: { cls: "badge-unknown", Icon: ShieldQuestion, label: "Unknown" },
};

export default function RiskBadge({ level, showLabel = true }) {
  const cfg = CONFIG[level] || CONFIG.UNKNOWN;
  const { Icon } = cfg;
  return (
    <span className={`badge ${cfg.cls}`}>
      <Icon />
      {showLabel ? cfg.label : level || "—"}
    </span>
  );
}
