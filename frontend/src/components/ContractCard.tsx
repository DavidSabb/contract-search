import { useState } from "react";
import type { Contract } from "../hooks/useContractSearch";
import "./ContractCard.css";

interface Props {
  contract: Contract;
}

const SOURCE_LABELS: Record<string, { label: string; className: string }> = {
  procuredata: { label: "\u{1F1E8}\u{1F1E6} ProcureData", className: "badge-ca" },
  open_canada: { label: "\u{1F1E8}\u{1F1E6} Open Canada", className: "badge-ca" },
  sam_gov: { label: "\u{1F1FA}\u{1F1F8} SAM.gov", className: "badge-us" },
  usa_spending: { label: "\u{1F1FA}\u{1F1F8} USASpending", className: "badge-us" },
};

function formatCurrency(value: number | null, currency: string): string {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

function relevanceColor(score: number): string {
  if (score >= 0.7) return "#059669";  // green
  if (score >= 0.4) return "#d97706";  // amber
  return "#ea580c";                     // orange
}

const STATUS_STYLES: Record<string, { label: string; className: string }> = {
  active:    { label: "Active",    className: "status-active" },
  closed:    { label: "Closed",    className: "status-closed" },
  awarded:   { label: "Awarded",   className: "status-awarded" },
  cancelled: { label: "Cancelled", className: "status-cancelled" },
  unknown:   { label: "Unknown",   className: "status-unknown" },
};

export default function ContractCard({ contract }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const source = SOURCE_LABELS[contract.source] || { label: contract.source, className: "" };

  const description = contract.description || "";
  const truncated = description.length > 150 && !expanded;
  const displayDesc = truncated ? description.slice(0, 150) + "..." : description;

  const dateLabel = contract.awarded_date
    ? `Awarded: ${formatDate(contract.awarded_date)}`
    : contract.close_date
      ? `Closes: ${formatDate(contract.close_date)}`
      : null;

  const score = contract.relevance_score ?? 0;
  const pct = Math.round(score * 100);
  const statusInfo = STATUS_STYLES[contract.status ?? "unknown"] ?? STATUS_STYLES.unknown;
  const inactive = contract.is_active === false;

  return (
    <div className={`contract-card ${inactive ? "card-inactive" : ""}`}>
      <div className="card-header">
        <h3 className="card-title">{contract.title}</h3>
        <div className="card-badges">
          <span className={`status-badge ${statusInfo.className}`}>
            {statusInfo.label}
          </span>
          {score > 0 && (
            <span
              className="relevance-badge"
              style={{ background: relevanceColor(score) }}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              {pct}% match
              {showTooltip && contract.matched_terms && contract.matched_terms.length > 0 && (
                <span className="relevance-tooltip">
                  Matched: {contract.matched_terms.slice(0, 3).join("; ")}
                </span>
              )}
            </span>
          )}
          <span className={`source-badge ${source.className}`}>{source.label}</span>
        </div>
      </div>

      <div className="card-meta">
        <span className="department">{contract.department}</span>
        {contract.vendor && <span className="vendor">Vendor: {contract.vendor}</span>}
      </div>

      <div className="card-details">
        <span className="value">{formatCurrency(contract.value, contract.currency)}</span>
        {dateLabel && <span className="date">{dateLabel}</span>}
      </div>

      {description && (
        <p className="card-description">
          {displayDesc}
          {description.length > 150 && (
            <button className="read-more" onClick={() => setExpanded(!expanded)}>
              {expanded ? "show less" : "read more"}
            </button>
          )}
        </p>
      )}

      {contract.url && (
        <a href={contract.url} target="_blank" rel="noopener noreferrer" className="view-original">
          View Original &rarr;
        </a>
      )}
    </div>
  );
}
