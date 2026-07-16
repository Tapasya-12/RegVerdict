import { useState } from "react";
import RippleButton from "./RippleButton";
import ExhibitCard from "./ExhibitCard";
import { toExhibitProps } from "../verdictUtils";

const API_BASE = "http://localhost:8000";

// Verdicts with a clear pass/fail direction. Requires Legal Review and
// Conflicting Regulations are deliberately excluded — neither is simply
// "better" or "worse" than Compliant/Non-Compliant, they're both "a human
// needs to look at this," which the banner logic below treats as its own
// category regardless of which direction the flip went.
const FAVORABILITY = { Compliant: 1, "Non-Compliant": -1 };
const ATTENTION_VERDICTS = new Set(["Requires Legal Review", "Conflicting Regulations"]);

function classifyBanner(originalVerdict, proposedVerdict, statusFlipped) {
  if (!statusFlipped) {
    return { tone: "neutral", message: "No change in compliance status." };
  }
  if (ATTENTION_VERDICTS.has(originalVerdict) || ATTENTION_VERDICTS.has(proposedVerdict)) {
    return { tone: "gold", message: "This change requires renewed legal review." };
  }
  const before = FAVORABILITY[originalVerdict] ?? 0;
  const after = FAVORABILITY[proposedVerdict] ?? 0;
  if (after > before) {
    return { tone: "green", message: "This change resolves the compliance issue." };
  }
  if (after < before) {
    return { tone: "red", message: "This change introduces a new violation." };
  }
  return { tone: "gold", message: "This change requires renewed legal review." };
}

export default function PolicyDiffView() {
  const [originalPolicy, setOriginalPolicy] = useState("");
  const [proposedChange, setProposedChange] = useState("");
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [comparisonId, setComparisonId] = useState(0);

  async function handleCompare() {
    if (!originalPolicy.trim() || !proposedChange.trim() || comparing) return;
    setComparing(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/simulate_policy_change`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          original_policy: originalPolicy.trim(),
          proposed_change: proposedChange.trim(),
        }),
      });
      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      setComparisonId((n) => n + 1);
    } catch (err) {
      console.error("simulate_policy_change failed:", err);
      setError("Could not reach the compliance engine — check that the backend is running.");
      setResult(null);
    } finally {
      setComparing(false);
    }
  }

  const banner = result
    ? classifyBanner(result.original_verdict?.verdict, result.proposed_verdict?.verdict, result.status_flipped)
    : null;

  return (
    <div>
      <div className="intake">
        <div className="intake-label">
          <span>Policy diff — compare current vs proposed</span>
          <span>SIMULATE_POLICY_CHANGE</span>
        </div>

        <div className="diff-fields">
          <div className="diff-field">
            <p className="diff-field-label">Current Policy</p>
            <textarea
              className="intake-field"
              placeholder="e.g. We charge a 2% processing fee on personal loans above ₹5 lakh."
              value={originalPolicy}
              onChange={(e) => setOriginalPolicy(e.target.value)}
            />
          </div>
          <div className="diff-field">
            <p className="diff-field-label">Proposed Change</p>
            <textarea
              className="intake-field"
              placeholder="e.g. We charge a 1.5% processing fee on personal loans above ₹5 lakh."
              value={proposedChange}
              onChange={(e) => setProposedChange(e.target.value)}
            />
          </div>
        </div>

        <div className="intake-footer">
          <span className="intake-hint">Runs check_compliance on both versions</span>
          <RippleButton className="submit-btn" onClick={handleCompare} disabled={comparing}>
            {comparing ? "Comparing…" : "Compare"}
          </RippleButton>
        </div>
      </div>

      {error && (
        <p className="intake-hint" style={{ color: "var(--seal-red)", marginTop: 24 }}>
          {error}
        </p>
      )}

      {result && (
        <>
          <div className={`diff-banner ${banner.tone}`}>{banner.message}</div>
          <div className="diff-columns">
            <div className="diff-column">
              <p className="diff-column-label">Before</p>
              <ExhibitCard
                key={`before-${comparisonId}`}
                index={0}
                isNewest={true}
                {...toExhibitProps(result.original_verdict)}
              />
            </div>
            <div className="diff-column">
              <p className="diff-column-label">After</p>
              <ExhibitCard
                key={`after-${comparisonId}`}
                index={1}
                isNewest={true}
                {...toExhibitProps(result.proposed_verdict)}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
