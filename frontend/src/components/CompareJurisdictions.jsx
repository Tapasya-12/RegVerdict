import { useEffect, useRef, useState } from "react";
import AssistantBubble from "./AssistantBubble";
import RetrievalTrace from "./RetrievalTrace";
import { apiFetch } from "../api";

function verdictOf(entry) {
  return entry?.verdict;
}

// Genuine disagreement only — "Requires Legal Review" on one side just means
// that regulator's corpus/policy match was too thin to ground a verdict, not
// a real conflict, so it's excluded the same way detect_regulatory_conflicts()
// excludes it server-side.
function hasDisagreement(entries) {
  const distinctVerdicts = new Set(
    entries.map(([, r]) => verdictOf(r)).filter((v) => v && v !== "Requires Legal Review")
  );
  return distinctVerdicts.size > 1;
}

let nextComparisonId = 0;

export default function CompareJurisdictions({ regulators }) {
  const [policyText, setPolicyText] = useState("");
  const [selectedRegulators, setSelectedRegulators] = useState(new Set(regulators));
  const [comparisons, setComparisons] = useState([]);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState(null);

  const threadRef = useRef(null);

  // regulators loads async (fetched once in App.jsx) — seed the checkbox
  // selection once it arrives rather than starting with an empty set.
  useEffect(() => {
    if (regulators.length > 0) {
      setSelectedRegulators((prev) => (prev.size === 0 ? new Set(regulators) : prev));
    }
  }, [regulators]);

  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [comparisons, comparing]);

  function toggleRegulator(reg) {
    setSelectedRegulators((prev) => {
      const next = new Set(prev);
      if (next.has(reg)) next.delete(reg);
      else next.add(reg);
      return next;
    });
  }

  async function handleCompare() {
    const chosen = regulators.filter((r) => selectedRegulators.has(r));
    if (!policyText.trim() || chosen.length === 0 || comparing) return;
    setComparing(true);
    setError(null);
    try {
      const res = await apiFetch("/api/compare_jurisdictions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ policy_text: policyText.trim(), regulators: chosen }),
      });
      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }
      const data = await res.json();
      setComparisons((prev) => [
        ...prev,
        { id: nextComparisonId++, policyText: policyText.trim(), entries: Object.entries(data.results_by_regulator) },
      ]);
      setPolicyText("");
    } catch (err) {
      console.error("compare_jurisdictions failed:", err);
      setError("Could not reach the compliance engine — check that the backend is running.");
    } finally {
      setComparing(false);
    }
  }

  return (
    <>
      <div className="chat-header">
        <div>
          <div className="chat-header-title">Compare Jurisdictions</div>
          <div className="chat-header-sub">Run the same policy against multiple regulators side by side.</div>
        </div>
        <div className="corpus-pill">{regulators.length ? regulators.join(" · ") : "…"}</div>
      </div>

      <div className="chat-thread" ref={threadRef}>
        {comparisons.map(({ id, policyText: submittedText, entries }) => (
          <div key={id}>
            <div className="msg-row user">
              <div className="bubble-user">{submittedText}</div>
            </div>
            {hasDisagreement(entries) && (
              <div className="result-banner plum" style={{ margin: "14px 0 16px" }}>
                These regulators disagree on this policy
              </div>
            )}
            <div className="diff-bubble-row" style={{ marginTop: entries.length ? 16 : 0 }}>
              {entries.map(([regulator, result]) => (
                <div className="diff-bubble-col" key={regulator}>
                  <p className="diff-bubble-col-label">{regulator}</p>
                  <AssistantBubble result={result} />
                </div>
              ))}
            </div>
          </div>
        ))}

        <RetrievalTrace active={comparing} />

        {error && (
          <p className="input-hint" style={{ color: "var(--seal-red)" }}>
            {error}
          </p>
        )}
      </div>

      <div className="input-bar-wrap">
        <div className="regulator-select">
          {regulators.map((reg) => (
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
        <div className="input-bar">
          <textarea
            rows="1"
            placeholder="Describe a business decision or policy…"
            value={policyText}
            onChange={(e) => setPolicyText(e.target.value)}
            disabled={comparing}
          />
          <button
            className="send-btn"
            onClick={handleCompare}
            disabled={comparing || !policyText.trim() || selectedRegulators.size === 0}
          >
            {comparing ? "Comparing…" : "Compare"}
          </button>
        </div>
        <div className="input-hint">Runs an independent grounded verdict per selected regulator.</div>
      </div>
    </>
  );
}
