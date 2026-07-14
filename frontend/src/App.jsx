import { useEffect, useState } from "react";
import Masthead from "./components/Masthead";
import IntakeForm from "./components/IntakeForm";
import ReviewingIndicator from "./components/ReviewingIndicator";
import ExhibitCard from "./components/ExhibitCard";
import AuditTrail from "./components/AuditTrail";

const API_BASE = "http://localhost:8000";

// tools.check_compliance() nests document/clause under source_clause (and
// returns it as null for the empty-corpus-match case, evidence_quote: "",
// grounding_verified: false); ExhibitCard's props are flat, per the design
// doc. This is the one seam between the two shapes — deliberately no
// placeholder fallback for document_name/clause_number here: ExhibitCard
// itself decides how to render the true no-match case ("no matching clause
// found") vs a real-but-ungrounded citation, and conflating the two by
// filling in a fallback string here would erase that distinction.
function toExhibitProps(result) {
  const source = result.source_clause || null;
  return {
    document_name: source?.document,
    clause_number: source?.clause_number,
    policy_summary: result.policy_summary,
    evidence_quote: result.evidence_quote,
    reasoning: result.reasoning,
    grounding_verified: result.grounding_verified,
    grounding_note: result.grounding_note,
    verdict: result.verdict,
    confidence: result.confidence,
  };
}

let nextExhibitId = 0;

export default function App() {
  const [activeTab, setActiveTab] = useState("workspace");
  const [exhibits, setExhibits] = useState([]);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState(null);
  const [indexedChunks, setIndexedChunks] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`health check returned ${res.status}`);
        return res.json();
      })
      .then((data) => setIndexedChunks(data.indexed_chunks))
      .catch((err) => {
        console.error("Backend health check failed:", err);
        setError("Could not reach the compliance engine — check that the backend is running.");
      });
  }, []);

  // Returns true on success, false on failure — IntakeForm uses this to
  // decide whether to clear its field (only on a real, grounded result).
  async function handleSubmit(policyText) {
    setReviewing(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/check_compliance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ policy_text: policyText }),
      });
      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }
      const result = await res.json();
      setExhibits((prev) => [...prev, { id: nextExhibitId++, ...toExhibitProps(result) }]);
      return true;
    } catch (err) {
      console.error("check_compliance failed:", err);
      setError("Could not reach the compliance engine — check that the backend is running.");
      return false;
    } finally {
      setReviewing(false);
    }
  }

  return (
    <>
      <div className="ambient"></div>
      <div className="grain"></div>
      <div className={`wrap${activeTab === "audit" ? " wrap-wide" : ""}`}>
        <Masthead />

        <div className="tab-bar">
          <button
            className={`tab-button${activeTab === "workspace" ? " active" : ""}`}
            onClick={() => setActiveTab("workspace")}
          >
            Workspace
          </button>
          <button
            className={`tab-button${activeTab === "audit" ? " active" : ""}`}
            onClick={() => setActiveTab("audit")}
          >
            Audit Trail
          </button>
        </div>

        {activeTab === "workspace" ? (
          <>
            <IntakeForm
              onSubmit={handleSubmit}
              disabled={reviewing}
              indexedClauseCount={indexedChunks ?? "…"}
            />
            <ReviewingIndicator active={reviewing} />
            {error && (
              <p className="intake-hint" style={{ color: "var(--seal-red)", marginBottom: 24 }}>
                {error}
              </p>
            )}
            <div className="results">
              {exhibits.map((exhibit, i) => (
                <ExhibitCard key={exhibit.id} index={i} isNewest={i === exhibits.length - 1} {...exhibit} />
              ))}
            </div>
          </>
        ) : (
          <AuditTrail />
        )}
      </div>
    </>
  );
}
