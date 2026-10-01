import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, ClipboardList } from "lucide-react";
import { api, apiErrorMessage } from "../api/client";
import { Loader, Banner, EmptyState, formatCurrency, formatDateTime } from "../components/Common";
import StatusBadge from "../components/StatusBadge";

const STATUSES = ["OPEN", "IN_PROGRESS", "CLOSED"];
const PRIORITIES = ["LOW", "MEDIUM", "HIGH"];

export default function InvestigationsPage() {
  const navigate = useNavigate();
  const [investigations, setInvestigations] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = { page, pageSize };
        if (status) params.status = status;
        if (priority) params.priority = priority;
        const { data } = await api.get("/api/investigations", { params });
        if (!cancelled) {
          setInvestigations(data.investigations || []);
          setTotal(data.total || 0);
        }
      } catch (err) {
        if (!cancelled) setError(apiErrorMessage(err, "Could not load investigations."));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [page, status, priority]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__eyebrow">Investigations</div>
          <h1>Open &amp; closed investigations</h1>
          <div className="page-header__meta">{total} investigations on file</div>
        </div>
      </div>

      <div className="filter-bar">
        <select
          className="select-input"
          value={status}
          onChange={(e) => {
            setPage(1);
            setStatus(e.target.value);
          }}
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replaceAll("_", " ")}
            </option>
          ))}
        </select>
        <select
          className="select-input"
          value={priority}
          onChange={(e) => {
            setPage(1);
            setPriority(e.target.value);
          }}
        >
          <option value="">All priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      {error && <Banner type="error">{error}</Banner>}

      <div className="card">
        {loading ? (
          <Loader label="Loading investigations…" />
        ) : investigations.length === 0 ? (
          <EmptyState title="No investigations match these filters" />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Investigation</th>
                <th>Claim</th>
                <th>Priority</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Decision</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {investigations.map((inv) => (
                <tr
                  key={inv.investigation_id}
                  className="clickable"
                  onClick={() => navigate(`/claims/${inv.claim_id}`)}
                >
                  <td className="mono">{inv.investigation_id}</td>
                  <td>
                    <div className="mono" style={{ fontWeight: 600 }}>
                      {inv.claim_id}
                    </div>
                    <div className="text-muted" style={{ fontSize: 12 }}>
                      {formatCurrency(inv.claims?.claim_amount)}
                    </div>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        inv.priority === "HIGH" ? "badge-high" : inv.priority === "MEDIUM" ? "badge-medium" : "badge-low"
                      }`}
                    >
                      {inv.priority}
                    </span>
                  </td>
                  <td className="text-secondary" style={{ maxWidth: 280 }}>
                    {inv.reason}
                  </td>
                  <td>
                    <StatusBadge value={inv.status} />
                  </td>
                  <td>{inv.final_decision ? inv.final_decision.replaceAll("_", " ") : "—"}</td>
                  <td className="text-secondary">{formatDateTime(inv.updated_at || inv.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {!loading && investigations.length > 0 && (
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
