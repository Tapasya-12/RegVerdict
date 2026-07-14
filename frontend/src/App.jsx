import { useState } from "react";
import Masthead from "./components/Masthead";
import IntakeForm from "./components/IntakeForm";
import ReviewingIndicator from "./components/ReviewingIndicator";
import ExhibitCard from "./components/ExhibitCard";

const API_URL = "http://localhost:8000/api/check_compliance";

// tools.check_compliance() nests document/clause under source_clause (and
// returns it as null for the empty-corpus-match case); ExhibitCard's props
// are flat, per the design doc. This is the one seam between the two shapes.
function toExhibitProps(result) {
  const source = result.source_clause || {};
  return {
    document_name: source.document || "unindexed corpus",
    clause_number: source.clause_number || "—",
    policy_summary: result.policy_summary,
    evidence_quote: result.evidence_quote,
    reasoning: result.reasoning,
    grounding_verified: result.grounding_verified,
    grounding_note: result.grounding_note,
    verdict: result.verdict,
    confidence: result.confidence,
  };
}

export default function App() {
  const [exhibits, setExhibits] = useState([]);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(policyText) {
    setReviewing(true);
    setError(null);
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ policy_text: policyText }),
      });
      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }
      const result = await res.json();
      setExhibits((prev) => [...prev, toExhibitProps(result)]);
    } catch (err) {
      console.error("check_compliance failed:", err);
      setError("Could not reach the compliance API — is api/server.py running on :8000?");
    } finally {
      setReviewing(false);
    }
  }

  return (
    <>
      <div className="ambient"></div>
      <div className="grain"></div>
      <div className="wrap">
        <Masthead />
        <IntakeForm onSubmit={handleSubmit} disabled={reviewing} indexedClauseCount={261} />
        <ReviewingIndicator active={reviewing} />
        {error && (
          <p className="intake-hint" style={{ color: "var(--seal-red)", marginBottom: 24 }}>
            {error}
          </p>
        )}
        <div className="results">
          {exhibits.map((exhibit, i) => (
            <ExhibitCard key={i} index={i} {...exhibit} />
          ))}
        </div>
      </div>
    </>
  );
}
