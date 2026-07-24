import { useState } from "react";
import { exportReportDocx } from "../api";

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
export default function AssistantBubble({ result, policyText }) {
  const source = result.source_clause;
  const tag = source ? `${source.document} §${source.clause_number}` : "no matching clause found";
  const hasQuote = !!result.evidence_quote && result.evidence_quote.trim().length > 0;
  const stampClass = STAMP_CLASS_BY_VERDICT[result.verdict] || "review";

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
      <div className="assistant-head">
        <span className="avatar">R</span>
        <span className="assistant-tag">
          {tag}
          {hasQuote && (
            <span className="preview">"{result.evidence_quote}" — full clause available in Clause Graph</span>
          )}
        </span>
      </div>
      <div className="assistant-body">
        <p className="assistant-summary">{result.policy_summary}</p>
        <div className="quote-block">
          <p className="quote-label">Verbatim evidence</p>
          <p className="quote-text">
            {hasQuote
              ? `"${result.evidence_quote}"`
              : "— no verbatim span could be matched against the retrieved clause —"}
          </p>
        </div>
        <p className="reasoning">{result.reasoning}</p>
        {exportError && (
          <p className="input-hint" style={{ color: "var(--seal-red)", marginBottom: 10 }}>
            {exportError}
          </p>
        )}
        <div className="assistant-footer">
          <div className="grounding-note">
            <span
              className="dot"
              style={!result.grounding_verified ? { background: "var(--seal-red)" } : undefined}
            ></span>
            {result.grounding_note ||
              (result.grounding_verified
                ? "Verified verbatim against source clause"
                : "No retrieved chunk could ground this claim.")}
          </div>
          <div className="assistant-footer-actions">
            {policyText && (
              <button className="export-docx-btn" onClick={handleExport} disabled={exporting}>
                {exporting ? "Exporting…" : "Export as Word"}
              </button>
            )}
            <span className={`stamp ${stampClass}`}>{result.verdict}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
