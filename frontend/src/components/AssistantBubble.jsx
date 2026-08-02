import { useState } from "react";
import { exportReportDocx } from "../api";
import { jurisdictionClass, jurisdictionCode } from "../jurisdiction";

const STAMP_CLASS_BY_VERDICT = {
  Compliant: "compliant",
  "Non-Compliant": "noncompliant",
  "Requires Legal Review": "review",
  "Conflicting Regulations": "conflict",
};

// Shared by every tool that renders a check_compliance-shaped verdict as a
// chat bubble (Workspace, Policy Diff's before/after pair, Compare
// Jurisdictions' per-regulator results) — one component, one look.
// policyText is the original submitted text (not result.policy_summary,
// which is the LLM's rephrased one-liner) — export needs it to re-run
// generate_compliance_report() server-side and get the same verdict back.
// regulators is the real, sorted list from /api/documents (via App.jsx) —
// it's what jurisdictionClass positionally assigns j1..j4 from, so the
// citation tag's color is never hardcoded to a specific regulator name.
export default function AssistantBubble({ result, policyText, regulators }) {
  const source = result.source_clause;
  const tag = source ? `${source.document} §${source.clause_number}` : "no matching clause found";
  const hasQuote = !!result.evidence_quote && result.evidence_quote.trim().length > 0;
  const stampClass = STAMP_CLASS_BY_VERDICT[result.verdict] || "review";

  const code = source ? jurisdictionCode(source.document) : null;
  const jClass = source ? jurisdictionClass(source.document, regulators) : null;

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState(null);

  async function handleExport() {
    if (exporting) return;
    setExporting(true);
    setExportError(null);
    try {
      await exportReportDocx(policyText);
    } catch (err) {
      console.error("export_report failed:", err);
      setExportError(err.message || "Could not export this report.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="bubble-assistant">
      <div className={`assistant-head${jClass ? ` ${jClass}` : ""}`}>
        {code && <span className={`jflag ${jClass}`}>{code}</span>}
        <span className="assistant-tag">
          {tag}
          {hasQuote && (
            <span className="preview">"{result.evidence_quote}" — full clause available in Clause Graph</span>
          )}
        </span>
      </div>
      <div className="assistant-body">
        <p className="assistant-summary">{result.policy_summary}</p>
        <div className={`quote-block${jClass ? ` ${jClass}` : ""}`}>
          <p className="quote-label">Verbatim evidence</p>
          <p className="quote-text">
            {hasQuote
              ? `"${result.evidence_quote}"`
              : "— no verbatim span could be matched against the retrieved clause —"}
          </p>
        </div>
        <p className="reasoning">{result.reasoning}</p>
        {exportError && (
          <p className="input-hint" style={{ color: "var(--status-red)", marginBottom: 10 }}>
            {exportError}
          </p>
        )}
        <div className="assistant-footer">
          <div className="assistant-footer-left">
            <div className="grounding-note">
              <span
                className="dot"
                style={!result.grounding_verified ? { background: "var(--status-red)" } : undefined}
              ></span>
              <span>
                {result.grounding_note ||
                  (result.grounding_verified
                    ? "Verified verbatim against source clause"
                    : "No retrieved chunk could ground this claim.")}
              </span>
            </div>
            {policyText && (
              <button className="export-link-btn" onClick={handleExport} disabled={exporting}>
                {exporting ? "Exporting…" : "Export as Word"}
              </button>
            )}
          </div>
          <span className={`stamp ${stampClass}`}>{result.verdict}</span>
        </div>
      </div>
    </div>
  );
}
