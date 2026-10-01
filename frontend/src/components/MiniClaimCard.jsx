import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge";
import { formatCurrency, formatDate } from "./Common";

export default function MiniClaimCard({ claim }) {
  const claimId = claim.claim_id;
  return (
    <Link to={`/claims/${claimId}`} className="mini-claim-card">
      <div className="mini-claim-card__id">{claimId}</div>
      <div className="mini-claim-card__amount">{formatCurrency(claim.claim_amount)}</div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span className="text-muted" style={{ fontSize: 11 }}>
          {formatDate(claim.claim_date)}
        </span>
        <StatusBadge value={claim.investigation_status} />
      </div>
    </Link>
  );
}
