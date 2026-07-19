// The "retrieval-trace" loading indicator — shared by every tool that waits
// on a real grounded-verdict call (Workspace, Policy Diff, Compare
// Jurisdictions), not generic typing dots.
export default function RetrievalTrace({ active }) {
  return (
    <div className={`typing-row${active ? " active" : ""}`}>
      <span className="typing-avatar">R</span>
      <div className="trace-box">
        <div className="trace-line">
          <span className="check">›</span> searching rbi_kyc_master_direction…
        </div>
        <div className="trace-line">
          <span className="check">›</span> searching rbi_interest_rate_advances…
        </div>
        <div className="trace-line">
          <span className="check">›</span> re-ranking 20 candidates…
        </div>
        <div className="trace-line">
          <span className="check">✓</span> verifying citation against source text…
        </div>
      </div>
    </div>
  );
}
