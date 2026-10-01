import { useEffect, useState } from "react";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { api, apiErrorMessage } from "../api/client";
import { Loader, Banner, EmptyState, formatDateTime } from "../components/Common";

export default function AuditLogPage() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [claimId, setClaimId] = useState("");
  const pageSize = 20;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = { page, pageSize };
        if (claimId) params.claimId = claimId;
        const { data } = await api.get("/api/audit-logs", { params });
        if (!cancelled) {
          setLogs(data.logs || []);
          setTotal(data.total || 0);
        }
      } catch (err) {
        if (!cancelled) setError(apiErrorMessage(err, "Could not load audit logs."));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [page, claimId]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const ACTION_COLOR = {
    AI_INVESTIGATION_FAILED: "badge-high",
    RECORDED_DECISION: "badge-accent",
    AI_INVESTIGATION_COMPLETED: "badge-low",
    STARTED_AI_INVESTIGATION: "badge-medium",
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__eyebrow">Administration</div>
          <h1>Audit log</h1>
          <div className="page-header__meta">{total} recorded actions</div>
        </div>
      </div>

      <div className="filter-bar">
        <div className="search-input">
          <Search />
          <input
            placeholder="Filter by claim ID…"
            value={claimId}
            onChange={(e) => {
              setPage(1);
              setClaimId(e.target.value);
            }}
          />
        </div>
      </div>

      {error && <Banner type="error">{error}</Banner>}

      <div className="card">
        {loading ? (
          <Loader label="Loading audit log…" />
        ) : logs.length === 0 ? (
          <EmptyState title="No audit entries found" />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Action</th>
                <th>Claim</th>
                <th>Details</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>
                    <span className={`badge ${ACTION_COLOR[log.action] || "badge-neutral"}`}>
                      {log.action.replaceAll("_", " ")}
                    </span>
                  </td>
                  <td className="mono">{log.claim_id || "—"}</td>
                  <td className="text-secondary" style={{ maxWidth: 320 }}>
                    {log.details || "—"}
                  </td>
                  <td className="text-secondary">{formatDateTime(log.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {!loading && logs.length > 0 && (
        <div className="pagination">
          <span>
            Page {page} of {totalPages} · {total} total
          </span>
          <div className="pagination__controls">
            <button
              className="pagination__btn"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft />
            </button>
            <button
              className="pagination__btn"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              <ChevronRight />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
