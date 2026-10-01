import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { AlertTriangle, FileWarning, Clock3, CheckCircle2, FolderKanban } from "lucide-react";
import { api, apiErrorMessage } from "../api/client";
import { Loader, Banner } from "../components/Common";

const RISK_COLORS = { LOW: "#2f6846", MEDIUM: "#9a6317", HIGH: "#a3342c" };

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [dashRes, analyticsRes] = await Promise.all([
          api.get("/api/dashboard"),
          api.get("/api/analytics?days=30"),
        ]);
        if (!cancelled) {
          setStats(dashRes.data);
          setAnalytics(analyticsRes.data);
        }
      } catch (err) {
        if (!cancelled) setError(apiErrorMessage(err, "Could not load dashboard data."));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const riskData = analytics
    ? ["LOW", "MEDIUM", "HIGH"].map((level) => ({
        level,
        count: analytics.risk_distribution?.[level] || 0,
      }))
    : [];

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__eyebrow">Overview</div>
          <h1>Dashboard</h1>
          <div className="page-header__meta">
            A daily read on claim volume, model-flagged risk, and open investigation load.
          </div>
        </div>
      </div>

      {error && <Banner type="error">{error}</Banner>}
      {loading && <Loader label="Loading dashboard…" />}

      {!loading && stats && (
        <>
          <div className="stat-row">
            <div className="stat-card stat-card--hero">
              <div className="stat-card__label">
                <FileWarning size={13} style={{ verticalAlign: "-2px", marginRight: 6 }} />
                Claims requiring investigation
              </div>
              <div className="stat-card__value">{stats.claims_requiring_investigation}</div>
              <div className="stat-card__foot">Flagged or currently under investigation</div>
            </div>

            <StatCard icon={<FolderKanban size={15} />} label="Total claims" value={stats.total_claims} />
            <StatCard
              icon={<AlertTriangle size={15} />}
              label="High risk claims"
              value={stats.high_risk_claims}
              accent="high"
            />
            <StatCard
              icon={<Clock3 size={15} />}
              label="Pending investigations"
              value={stats.pending_investigations}
              accent="medium"
            />
            <StatCard
              icon={<CheckCircle2 size={15} />}
              label="Reviewed today"
              value={stats.claims_reviewed_today}
              accent="low"
            />
          </div>

          <div className="card-grid">
            <div className="span-8 card">
              <div className="card__header">
                <div className="card__title">Claims filed over time</div>
                <span className="text-muted" style={{ fontSize: 12 }}>Last 30 days</span>
              </div>
              <div className="card__body">
                {analytics?.claims_over_time?.length ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={analytics.claims_over_time}>
                      <CartesianGrid stroke="var(--border)" vertical={false} />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                        axisLine={{ stroke: "var(--border)" }}
                        tickLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                        axisLine={false}
                        tickLine={false}
                        width={44}
                      />
                      <Tooltip
                        contentStyle={{
                          fontSize: 12,
                          border: "1px solid var(--border)",
                          borderRadius: 6,
                          fontFamily: "var(--font-body)",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="count"
                        stroke="var(--accent)"
                        strokeWidth={2.25}
                        dot={false}
                        activeDot={{ r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state">
                    <div className="empty-state__title">No claim volume yet</div>
                  </div>
                )}
              </div>
            </div>

            <div className="span-4 card">
              <div className="card__header">
                <div className="card__title">Risk distribution</div>
              </div>
              <div className="card__body">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={riskData}>
                    <CartesianGrid stroke="var(--border)" vertical={false} />
                    <XAxis
                      dataKey="level"
                      tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                      axisLine={{ stroke: "var(--border)" }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                      axisLine={false}
                      tickLine={false}
                      width={44}
                    />
                    <Tooltip
                      contentStyle={{
                        fontSize: 12,
                        border: "1px solid var(--border)",
                        borderRadius: 6,
                        fontFamily: "var(--font-body)",
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {riskData.map((entry) => (
                        <Cell key={entry.level} fill={RISK_COLORS[entry.level]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, accent }) {
  const color = accent === "high" ? "var(--risk-high)" : accent === "medium" ? "var(--risk-medium)" : accent === "low" ? "var(--risk-low)" : "var(--text-secondary)";
  return (
    <div className="stat-card">
      <div className="stat-card__label" style={{ display: "flex", alignItems: "center", gap: 6, color }}>
        {icon} {label}
      </div>
      <div className="stat-card__value">{value ?? "—"}</div>
    </div>
  );
}
