const COLOR = {
  LOW: "var(--risk-low)",
  MEDIUM: "var(--risk-medium)",
  HIGH: "var(--risk-high)",
  UNKNOWN: "var(--risk-unknown)",
};

export default function RiskGauge({ probability = 0, level = "UNKNOWN", size = 108 }) {
  const stroke = 9;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(1, probability || 0));
  const dash = circumference * pct;
  const color = COLOR[level] || COLOR.UNKNOWN;

  return (
    <div className="risk-gauge__ring" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
      </svg>
      <div className="risk-gauge__ring-value">
        <span className="risk-gauge__pct" style={{ color }}>
          {Math.round(pct * 100)}%
        </span>
        <span className="risk-gauge__pct-label">Risk score</span>
      </div>
    </div>
  );
}
