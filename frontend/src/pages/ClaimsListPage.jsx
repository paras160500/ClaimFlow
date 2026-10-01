import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, ChevronLeft, ChevronRight, FileSearch } from "lucide-react";
import { api, apiErrorMessage } from "../api/client";
import { Loader, Banner, EmptyState, formatCurrency, formatDate } from "../components/Common";
import StatusBadge from "../components/StatusBadge";

const CLAIM_TYPES = ["ACCIDENT", "THEFT", "FIRE", "NATURAL_DISASTER", "VANDALISM"];
const STATUSES = ["SUBMITTED", "UNDER_REVIEW", "CLOSED"];
const INVESTIGATION_STATUSES = ["NOT_FLAGGED", "FLAGGED", "INVESTIGATED"];

export default function ClaimsListPage() {
  const navigate = useNavigate();
  const [claims, setClaims] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [investigationStatus, setInvestigationStatus] = useState("");
  const [claimType, setClaimType] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = { page, pageSize };
        if (search) params.search = search;
        if (status) params.status = status;
        if (investigationStatus) params.investigationStatus = investigationStatus;
        if (claimType) params.claimType = claimType;

        const { data } = await api.get("/api/claims", { params });
        if (!cancelled) {
          setClaims(data.claims || []);
          setTotal(data.total || 0);
        }
      } catch (err) {
        if (!cancelled) setError(apiErrorMessage(err, "Could not load claims."));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, search, status, investigationStatus, claimType]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__eyebrow">Claims</div>
          <h1>All claims</h1>
          <div className="page-header__meta">{total} claims on file</div>
        </div>
      </div>

      <div className="filter-bar">
        <div className="search-input">
          <Search />
          <input
            placeholder="Search claim ID, policy ID, or vehicle ID…"
            value={search}
            onChange={(e) => {
              setPage(1);
              setSearch(e.target.value);
            }}
          />
        </div>
        <select
          className="select-input"
          value={claimType}
          onChange={(e) => {
            setPage(1);
            setClaimType(e.target.value);
          }}
        >
          <option value="">All claim types</option>
          {CLAIM_TYPES.map((t) => (
            <option key={t} value={t}>
              {t.replaceAll("_", " ")}
            </option>
          ))}
        </select>
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
          value={investigationStatus}
          onChange={(e) => {
            setPage(1);
            setInvestigationStatus(e.target.value);
          }}
        >
          <option value="">All investigation statuses</option>
          {INVESTIGATION_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </div>

      {error && <Banner type="error">{error}</Banner>}

      <div className="card">
        {loading ? (
          <Loader label="Loading claims…" />
        ) : claims.length === 0 ? (
          <EmptyState
            title="No claims match these filters"
            hint="Try clearing a filter or searching a different term."
          />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Claim</th>
                <th>Vehicle</th>
                <th>Amount</th>
                <th>Type</th>
                <th>Status</th>
                <th>Investigation</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((c) => (
                <tr key={c.claim_id} className="clickable" onClick={() => navigate(`/claims/${c.claim_id}`)}>
                  <td>
                    <div className="mono" style={{ fontWeight: 600 }}>
                      {c.claim_id}
                    </div>
                    <div className="text-muted" style={{ fontSize: 12 }}>
                      {c.customers?.full_name || c.customer_id}
                    </div>
                  </td>
                  <td>
                    {c.vehicles ? `${c.vehicles.make} ${c.vehicles.model}` : c.vehicle_id}
                  </td>
                  <td className="mono">{formatCurrency(c.claim_amount)}</td>
                  <td>{c.claim_type?.replaceAll("_", " ")}</td>
                  <td>
                    <StatusBadge value={c.status} />
                  </td>
                  <td>
                    <StatusBadge value={c.investigation_status} />
                  </td>
                  <td className="text-secondary">{formatDate(c.claim_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {!loading && claims.length > 0 && (
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
