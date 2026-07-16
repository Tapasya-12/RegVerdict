import { useState } from "react";
import RippleButton from "./RippleButton";
import ExhibitCard from "./ExhibitCard";
import { toExhibitProps } from "../verdictUtils";

const API_BASE = "http://localhost:8000";

// Hardcoded to the regulators actually present in the indexed corpus (see
// data/document_manifest.json) rather than a dynamic backend lookup — only
// 2 exist today, and silently offering a regulator with zero indexed
// clauses would just produce a "no matching clause" card. Revisit with a
// real /api/regulators endpoint once a 3rd is ingested.
const AVAILABLE_REGULATORS = ["RBI", "GDPR"];

// results_by_regulator entries are either a full VerdictOutput dict or,
// when a regulator has no indexed clauses at all, a bare
// {verdict, reasoning, confidence} dict — both carry "verdict" directly.
function verdictOf(entry) {
  return entry?.verdict;
}

export default function JurisdictionComparator() {
  const [policyText, setPolicyText] = useState("");
  const [selectedRegulators, setSelectedRegulators] = useState(new Set(AVAILABLE_REGULATORS));
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [comparisonId, setComparisonId] = useState(0);

  function toggleRegulator(reg) {
    setSelectedRegulators((prev) => {
      const next = new Set(prev);
      if (next.has(reg)) next.delete(reg);
      else next.add(reg);
      return next;
    });
  }

  async function handleCompare() {
    const regulators = AVAILABLE_REGULATORS.filter((r) => selectedRegulators.has(r));
    if (!policyText.trim() || regulators.length === 0 || comparing) return;
    setComparing(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/compare_jurisdictions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ policy_text: policyText.trim(), regulators }),
      });
      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      setComparisonId((n) => n + 1);
    } catch (err) {
      console.error("compare_jurisdictions failed:", err);
      setError("Could not reach the compliance engine — check that the backend is running.");
      setResult(null);
    } finally {
      setComparing(false);
    }
  }

  const entries = result ? Object.entries(result.results_by_regulator) : [];
  // Genuine disagreement only — "Requires Legal Review" on one side just
  // means that regulator's corpus/policy match was too thin to ground a
  // verdict, not a real conflict, so it's excluded the same way
  // detect_regulatory_conflicts() excludes it server-side.
  const distinctVerdicts = new Set(
    entries.map(([, r]) => verdictOf(r)).filter((v) => v && v !== "Requires Legal Review")
  );
  const disagreement = distinctVerdicts.size > 1;

  return (
    <div>
      <div className="intake">
        <div className="intake-label">
          <span>Jurisdiction comparator — same policy, multiple regulators</span>
          <span>COMPARE_JURISDICTIONS</span>
        </div>

        <textarea
          className="intake-field"
          placeholder="e.g. We retain customer KYC records for 3 years after account closure."
          value={policyText}
          onChange={(e) => setPolicyText(e.target.value)}
        />

        <div className="regulator-select">
          {AVAILABLE_REGULATORS.map((reg) => (
            <label className="regulator-checkbox" key={reg}>
              <input
                type="checkbox"
                checked={selectedRegulators.has(reg)}
                onChange={() => toggleRegulator(reg)}
              />
              {reg}
            </label>
          ))}
        </div>

        <div className="intake-footer">
          <span className="intake-hint">Runs an independent grounded verdict per selected regulator</span>
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
          {disagreement && (
            <div className="diff-banner plum">These regulators disagree on this policy</div>
          )}
          <div className="diff-columns">
            {entries.map(([regulator, verdictResult], i) => (
              <div className="diff-column" key={`${regulator}-${comparisonId}`}>
                <p className="diff-column-label">{regulator}</p>
                <ExhibitCard index={i} isNewest={true} {...toExhibitProps(verdictResult)} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
