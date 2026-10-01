import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  ListChecks,
  GitBranch,
  BookOpen,
  MessagesSquare,
  Gavel,
  CircleCheck,
  CircleAlert,
  CircleX,
  RefreshCw,
  Wrench,
  Car,
  FileText,
} from "lucide-react";
import { api, apiErrorMessage } from "../api/client";
import { Loader, Banner, formatCurrency, formatDate, formatDateTime } from "../components/Common";
import RiskBadge from "../components/RiskBadge";
import StatusBadge from "../components/StatusBadge";
import RiskGauge from "../components/RiskGauge";
import MiniClaimCard from "../components/MiniClaimCard";
import { useAuth } from "../context/AuthContext";

const DECISIONS = [
  { value: "APPROVE", label: "Approve" },
  { value: "REQUEST_DOCUMENTS", label: "Request Documents" },
  { value: "INVESTIGATE_FURTHER", label: "Investigate Further" },
  { value: "REJECT", label: "Reject" },
];

const RULE_ICON = { PASS: CircleCheck, WARN: CircleAlert, FAIL: CircleX };
const RULE_CLASS = { PASS: "pass", WARN: "warn", FAIL: "fail" };

export default function ClaimDetailPage() {
  const { claimId } = useParams();
  const navigate = useNavigate();
  const { hasRole, employee } = useAuth();

  const [claim, setClaim] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [aiResult, setAiResult] = useState(null);
  const [aiError, setAiError] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  const [decision, setDecision] = useState("");
  const [note, setNote] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [decisionError, setDecisionError] = useState("");

  const loadClaim = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [claimRes, historyRes] = await Promise.all([
        api.get(`/api/claims/${claimId}`),
        api.get(`/api/claims/${claimId}/history`),
      ]);
      setClaim(claimRes.data.claim);
      setHistory(historyRes.data.investigations || []);
    } catch (err) {
      setError(apiErrorMessage(err, "Could not load this claim."));
    } finally {
      setLoading(false);
    }
  }, [claimId]);

  useEffect(() => {
    loadClaim();
  }, [loadClaim]);

  async function runAnalysis() {
    setAnalyzing(true);
    setAiError("");
    try {
      const { data } = await api.post(`/api/claims/${claimId}/analyze`);
      setClaim(data.claim);
      if (data.ai) {
        setAiResult(data.ai);
      } else {
        setAiError(data.ai_error || "AI investigation summary is temporarily unavailable.");
      }
      loadClaim();
    } catch (err) {
      setAiError(apiErrorMessage(err, "AI investigation failed to run."));
    } finally {
      setAnalyzing(false);
    }
  }

  const openInvestigation =
    history.find((inv) => inv.status === "OPEN" || inv.status === "IN_PROGRESS") || null;

  async function submitDecision() {
    if (!decision || !openInvestigation) return;
    setSubmittingDecision(true);
    setDecisionError("");
    try {
      await api.post(`/api/investigations/${openInvestigation.investigation_id}/decision`, {
        decision,
        note: note || undefined,
      });
      setDecision("");
      setNote("");
      await loadClaim();
    } catch (err) {
      setDecisionError(apiErrorMessage(err, "Could not record decision."));
    } finally {
      setSubmittingDecision(false);
    }
  }

  if (loading) {
    return (
      <div className="page">
        <Loader label="Loading claim…" />
      </div>
    );
  }

  if (error || !claim) {
    return (
      <div className="page">
        <Banner type="error">{error || "Claim not found."}</Banner>
        <button className="btn btn-secondary" onClick={() => navigate("/claims")}>
          <ArrowLeft /> Back to claims
        </button>
      </div>
    );
  }

  const policy = claim.policies;
  const customer = claim.customers;
  const vehicle = claim.vehicles;
  const repairShop = claim.repair_shops;

  return (
    <div className="page">
      <button className="btn btn-ghost btn-sm" onClick={() => navigate("/claims")} style={{ marginBottom: 18 }}>
        <ArrowLeft /> All claims
      </button>

      {/* ---- Header ---- */}
      <div
        className="card"
        style={{
          padding: "24px 28px",
          marginBottom: 24,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 20,
        }}
      >
        <div>
          <div className="page-header__eyebrow mono">{claim.claim_id}</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginTop: 4 }}>
            <span className="mono" style={{ fontFamily: "var(--font-display)", fontSize: 32, fontWeight: 700 }}>
              {formatCurrency(claim.claim_amount)}
            </span>
            <StatusBadge value={claim.status} />
            <StatusBadge value={claim.investigation_status} />
          </div>
          <div className="text-secondary" style={{ marginTop: 6, fontSize: 13 }}>
            {claim.claim_type?.replaceAll("_", " ")} claim · filed {formatDate(claim.claim_date)} · incident{" "}
            {formatDate(claim.incident_date)}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {aiResult && <RiskGauge probability={aiResult.risk_probability} level={aiResult.risk_level} size={84} />}
          {hasRole("ADMIN", "INVESTIGATOR") && (
            <button className="btn btn-primary" onClick={runAnalysis} disabled={analyzing}>
              {analyzing ? <RefreshCw className="spin-icon" /> : <Sparkles />}
              {analyzing ? "Analyzing…" : aiResult ? "Re-run AI Investigation" : "Run AI Investigation"}
            </button>
          )}
        </div>
      </div>

      {aiError && <Banner type="warning">{aiError}</Banner>}

      <div className="card-grid">
        {/* ---- Claim information ---- */}
        <div className="span-6 card">
          <div className="card__header">
            <div className="card__title">
              <FileText /> Claim information
            </div>
          </div>
          <div className="card__body">
            <div className="info-grid">
              <div className="info-grid__item">
                <label>Customer</label>
                <div>{customer?.full_name || claim.customer_id}</div>
              </div>
              <div className="info-grid__item">
                <label>Vehicle</label>
                <div>
                  <Car size={13} style={{ verticalAlign: "-2px", marginRight: 4 }} />
                  {vehicle ? `${vehicle.make} ${vehicle.model} (${vehicle.manufacture_year})` : claim.vehicle_id}
                </div>
              </div>
              <div className="info-grid__item">
                <label>Policy</label>
                <div>
                  {claim.policy_id} · {policy?.policy_type}
                </div>
              </div>
              <div className="info-grid__item">
                <label>Coverage limit</label>
                <div>{formatCurrency(policy?.coverage_limit)}</div>
              </div>
              <div className="info-grid__item">
                <label>Repair shop</label>
                <div>
                  <Wrench size={13} style={{ verticalAlign: "-2px", marginRight: 4 }} />
                  {repairShop?.name || claim.repair_shop_id || "—"}
                </div>
              </div>
              <div className="info-grid__item">
                <label>Vehicle value</label>
                <div>{formatCurrency(vehicle?.vehicle_value)}</div>
              </div>
            </div>
            {claim.description && (
              <>
                <hr className="divider" />
                <div className="info-grid__item">
                  <label>Description</label>
                  <div style={{ fontWeight: 400 }}>{claim.description}</div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* ---- ML Risk Assessment ---- */}
        <div className="span-6 card">
          <div className="card__header">
            <div className="card__title">
              <ShieldCheck /> ML risk assessment
            </div>
            {aiResult && <RiskBadge level={aiResult.risk_level} />}
          </div>
          <div className="card__body">
            {!aiResult ? (
              <div className="empty-state" style={{ padding: "24px 12px" }}>
                <Sparkles />
                <div className="empty-state__title">No risk assessment yet</div>
                <div>Run an AI investigation to generate a model-based risk score.</div>
              </div>
            ) : (
              <div className="risk-gauge">
                <RiskGauge probability={aiResult.risk_probability} level={aiResult.risk_level} />
                <div>
                  <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-secondary)" }}>
                    Model version <span className="mono">{aiResult.model_version}</span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8, lineHeight: 1.5 }}>
                    {aiResult.disclaimer}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ---- Rule checks ---- */}
        <div className="span-6 card">
          <div className="card__header">
            <div className="card__title">
              <ListChecks /> Rule checks
            </div>
          </div>
          <div className="card__body">
            {!aiResult ? (
              <div className="empty-state" style={{ padding: "24px 12px" }}>
                <div className="empty-state__title">Not yet evaluated</div>
              </div>
            ) : (
              aiResult.rule_results?.map((rule) => {
                const Icon = RULE_ICON[rule.status] || CircleAlert;
                return (
                  <div className="rule-row" key={rule.rule}>
                    <div className={`rule-row__icon ${RULE_CLASS[rule.status]}`}>
                      <Icon />
                    </div>
                    <div>
                      <div className="rule-row__name">{rule.rule.replaceAll("_", " ")}</div>
                      <div className="rule-row__message">{rule.message}</div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* ---- Relationship analysis ---- */}
        <div className="span-6 card">
          <div className="card__header">
            <div className="card__title">
              <GitBranch /> Relationship analysis
            </div>
          </div>
          <div className="card__body">
            {!aiResult ? (
              <div className="empty-state" style={{ padding: "24px 12px" }}>
                <div className="empty-state__title">Not yet evaluated</div>
              </div>
            ) : (
              <>
                <div className="relationship-stat-row">
                  <div className="relationship-stat">
                    <div className="relationship-stat__value">
                      {aiResult.relationships?.repair_shop?.total_claims ?? 0}
                    </div>
                    <div className="relationship-stat__label">Repair shop claims</div>
                  </div>
                  <div className="relationship-stat">
                    <div className="relationship-stat__value">
                      {aiResult.relationships?.repair_shop?.investigated_claims ?? 0}
                    </div>
                    <div className="relationship-stat__label">Previously investigated</div>
                  </div>
                  <div className="relationship-stat">
                    <div className="relationship-stat__value">
                      {aiResult.relationships?.customer?.total_claims ?? 0}
                    </div>
                    <div className="relationship-stat__label">Customer claims</div>
                  </div>
                </div>

                {aiResult.relationships?.repair_shop?.sample_claims?.length > 0 && (
                  <>
                    <div className="section-label">Other claims at this repair shop</div>
                    <div className="mini-claim-grid">
                      {aiResult.relationships.repair_shop.sample_claims.slice(0, 6).map((c) => (
                        <MiniClaimCard key={c.claim_id} claim={c} />
                      ))}
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>

        {/* ---- Policy evidence ---- */}
        <div className="span-6 card">
          <div className="card__header">
            <div className="card__title">
              <BookOpen /> Retrieved policy evidence
            </div>
          </div>
          <div className="card__body">
            {!aiResult || aiResult.retrieved_policy_evidence?.length === 0 ? (
              <div className="empty-state" style={{ padding: "24px 12px" }}>
                <div className="empty-state__title">No evidence retrieved yet</div>
              </div>
            ) : (
              aiResult.retrieved_policy_evidence.map((e, i) => (
                <div className="evidence-item" key={i}>
                  "{e.text}"
                  <div className="evidence-item__meta">
                    <span>{e.metadata?.policy_type}</span>
                    <span>{e.metadata?.section}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ---- Investigator notes ---- */}
        <div className="span-6 card">
          <div className="card__header">
            <div className="card__title">
              <MessagesSquare /> Related investigator notes
            </div>
          </div>
          <div className="card__body">
            {!aiResult || aiResult.retrieved_investigator_notes?.length === 0 ? (
              <div className="empty-state" style={{ padding: "24px 12px" }}>
                <div className="empty-state__title">No related notes retrieved yet</div>
              </div>
            ) : (
              aiResult.retrieved_investigator_notes.map((n, i) => (
                <div className="evidence-item" key={i}>
                  {n.text}
                </div>
              ))
            )}
          </div>
        </div>

        {/* ---- AI Summary ---- */}
        {aiResult && (
          <div className="span-8 card">
            <div className="card__header">
              <div className="card__title">
                <Sparkles /> AI investigation summary
              </div>
            </div>
            <div className="card__body">
              <div className="ai-summary">{aiResult.summary}</div>
              <div className="ai-summary-source">
                <span className="badge badge-accent">
                  {aiResult.summary_source === "llm" ? "LLM-generated" : "Deterministic fallback"}
                </span>
                <span className="text-muted" style={{ fontSize: 12 }}>
                  {aiResult.summary_source === "llm"
                    ? "Generated from the evidence above by the AI model."
                    : "The AI model was unavailable — this summary was built directly from the rule and risk data above."}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* ---- Decision panel ---- */}
        <div className={aiResult ? "span-4 card" : "span-6 card"}>
          <div className="card__header">
            <div className="card__title">
              <Gavel /> Investigator decision
            </div>
          </div>
          <div className="card__body">
            {!openInvestigation ? (
              <div className="empty-state" style={{ padding: "16px 8px" }}>
                <div className="empty-state__title">No open investigation</div>
                <div style={{ fontSize: 12.5 }}>
                  {aiResult
                    ? "This claim's risk level didn't require opening an investigation."
                    : "Run an AI investigation — one opens automatically for medium/high risk claims."}
                </div>
              </div>
            ) : !hasRole("ADMIN", "INVESTIGATOR") ? (
              <div className="empty-state" style={{ padding: "16px 8px" }}>
                <div className="empty-state__title">View only</div>
                <div style={{ fontSize: 12.5 }}>Only Admins and Investigators can record a decision.</div>
              </div>
            ) : (
              <>
                <div className="section-label">
                  {openInvestigation.priority} priority · {openInvestigation.reason}
                </div>
                <div className="decision-grid">
                  {DECISIONS.map((d) => (
                    <button
                      key={d.value}
                      className={`decision-btn${decision === d.value ? " selected" : ""}`}
                      onClick={() => setDecision(d.value)}
                    >
                      {d.label}
                    </button>
                  ))}
                </div>
                <textarea
                  className="decision-note"
                  placeholder="Add a note for the record (optional)…"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
                {decisionError && <Banner type="error">{decisionError}</Banner>}
                <button
                  className="btn btn-primary btn-block"
                  disabled={!decision || submittingDecision}
                  onClick={submitDecision}
                >
                  {submittingDecision ? "Saving…" : "Record decision"}
                </button>
              </>
            )}

            {history.length > 0 && (
              <>
                <hr className="divider" />
                <div className="section-label">Investigation history</div>
                <div className="timeline">
                  {history.map((inv) => (
                    <div className="timeline-item" key={inv.investigation_id}>
                      <div className="timeline-item__title">
                        {inv.final_decision ? inv.final_decision.replaceAll("_", " ") : inv.status}
                      </div>
                      <div className="timeline-item__meta">
                        {formatDateTime(inv.updated_at || inv.created_at)} · {employee?.name || "—"}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
