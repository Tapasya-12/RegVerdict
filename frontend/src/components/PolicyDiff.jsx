import { useEffect, useRef, useState } from "react";
import AssistantBubble from "./AssistantBubble";
import RetrievalTrace from "./RetrievalTrace";
import { apiFetch } from "../api";

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
    return { tone: "review", message: "This change requires renewed legal review." };
  }
  const before = FAVORABILITY[originalVerdict] ?? 0;
  const after = FAVORABILITY[proposedVerdict] ?? 0;
  if (after > before) {
    return { tone: "green", message: "This change resolves the compliance issue." };
  }
  if (after < before) {
    return { tone: "red", message: "This change introduces a new violation." };
  }
  return { tone: "review", message: "This change requires renewed legal review." };
}

let nextComparisonId = 0;

export default function PolicyDiff({ regulators }) {
  const [originalPolicy, setOriginalPolicy] = useState("");
  const [proposedChange, setProposedChange] = useState("");
  const [comparisons, setComparisons] = useState([]);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState(null);

  const threadRef = useRef(null);

  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [comparisons, comparing]);

  async function handleCompare() {
    if (!originalPolicy.trim() || !proposedChange.trim() || comparing) return;
    setComparing(true);
    setError(null);
    try {
      const res = await apiFetch("/api/simulate_policy_change", {
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
      setComparisons((prev) => [
        ...prev,
        {
          id: nextComparisonId++,
          data,
          originalPolicyText: originalPolicy.trim(),
          proposedChangeText: proposedChange.trim(),
        },
      ]);
      setOriginalPolicy("");
      setProposedChange("");
    } catch (err) {
      console.error("simulate_policy_change failed:", err);
      setError("Could not reach the compliance engine — check that the backend is running.");
    } finally {
      setComparing(false);
    }
  }

  return (
    <>
      <div className="chat-header">
        <div>
          <div className="chat-header-title">Policy Diff</div>
          <div className="chat-header-sub">Compare a current policy against a proposed change.</div>
        </div>
        <div className="corpus-pill">{regulators.length ? regulators.join(" · ") : "…"}</div>
      </div>

      <div className="chat-thread" ref={threadRef}>
        {comparisons.map(({ id, data, originalPolicyText, proposedChangeText }) => {
          const banner = classifyBanner(
            data.original_verdict?.verdict,
            data.proposed_verdict?.verdict,
            data.status_flipped
          );
          return (
            <div key={id}>
              <div className={`result-banner ${banner.tone}`} style={{ marginBottom: 16 }}>
                {banner.message}
              </div>
              <div className="diff-bubble-row">
                <div className="diff-bubble-col">
                  <p className="diff-bubble-col-label">Before</p>
                  <AssistantBubble result={data.original_verdict} policyText={originalPolicyText} />
                </div>
                <div className="diff-bubble-col">
                  <p className="diff-bubble-col-label">After</p>
                  <AssistantBubble result={data.proposed_verdict} policyText={proposedChangeText} />
                </div>
              </div>
            </div>
          );
        })}

        <RetrievalTrace active={comparing} />

        {error && (
          <p className="input-hint" style={{ color: "var(--seal-red)" }}>
            {error}
          </p>
        )}
      </div>

      <div className="input-bar-wrap">
        <div className="diff-stack">
          <div className="diff-input-group">
            <p className="diff-input-label">Current Policy</p>
            <div className="input-bar">
              <textarea
                rows="2"
                placeholder="e.g. We charge a 2% processing fee on personal loans above ₹5 lakh."
                value={originalPolicy}
                onChange={(e) => setOriginalPolicy(e.target.value)}
                disabled={comparing}
              />
            </div>
          </div>
          <div className="diff-input-group">
            <p className="diff-input-label">Proposed Change</p>
            <div className="input-bar">
              <textarea
                rows="2"
                placeholder="e.g. We charge a 1.5% processing fee on personal loans above ₹5 lakh."
                value={proposedChange}
                onChange={(e) => setProposedChange(e.target.value)}
                disabled={comparing}
              />
            </div>
          </div>
        </div>
        <div className="diff-compare-footer">
          <span className="input-hint">Runs check_compliance on both versions</span>
          <button
            className="send-btn"
            onClick={handleCompare}
            disabled={comparing || !originalPolicy.trim() || !proposedChange.trim()}
          >
            {comparing ? "Comparing…" : "Compare"}
          </button>
        </div>
      </div>
    </>
  );
}
