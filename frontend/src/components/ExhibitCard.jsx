import { useRef } from "react";

// A small set of tilts to cycle through as the exhibit list grows — the
// prototype only hardcoded 3 (via :nth-of-type), but this is a chat-style
// thread that can grow without bound, so cards cycle through this set by
// position instead of being pinned to a fixed nth-of-type rule.
const TILTS = [0, -0.6, 0.5, -0.4, 0.6, -0.3, 0.4, -0.5];
const SEQ_STEP_SECONDS = 0.5;

const STAMP_CLASS_BY_VERDICT = {
  Compliant: "compliant",
  "Non-Compliant": "noncompliant",
  "Requires Legal Review": "review",
  "Conflicting Regulations": "conflict",
};

const STAMP_LABEL_BY_VERDICT = {
  Compliant: "Compliant",
  "Non-Compliant": "Non-Compliant",
  "Requires Legal Review": "Review",
  "Conflicting Regulations": "Conflict",
};

export default function ExhibitCard({
  index,
  document_name,
  clause_number,
  policy_summary,
  evidence_quote,
  reasoning,
  grounding_verified,
  grounding_note,
  verdict,
  confidence,
}) {
  const cardRef = useRef(null);

  const tilt = TILTS[index % TILTS.length];
  const seq = index * SEQ_STEP_SECONDS;

  const isNoisyTier = !!grounding_note && /noise-tolerant/i.test(grounding_note);
  const hasQuote = !!evidence_quote && evidence_quote.trim().length > 0;
  const belowThreshold = typeof confidence === "number" && confidence < 0.9;

  function handleMouseMove(e) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const card = cardRef.current;
    if (!card) return;
    const r = card.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    card.style.transform = `perspective(900px) rotateX(${py * -5}deg) rotateY(${px * 6}deg) rotate(${tilt}deg) translateY(0)`;
  }

  function handleMouseLeave() {
    const card = cardRef.current;
    if (card) card.style.transform = "";
  }

  return (
    <div
      ref={cardRef}
      className="exhibit"
      style={{ "--tilt": `${tilt}deg`, "--seq": `${seq}s` }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <span className="exhibit-tab">
        EXHIBIT — {document_name} §{clause_number}
      </span>
      <div className="exhibit-body">
        <p className="exhibit-summary">{policy_summary}</p>

        <div className="quote-block">
          <p className="quote-label">Verbatim evidence</p>
          <p className="quote-text">
            {hasQuote ? `"${evidence_quote}"` : "— no verbatim span could be matched against the retrieved clause —"}
          </p>
        </div>

        <p className="reasoning">{reasoning}</p>

        <div className="exhibit-footer">
          {grounding_verified ? (
            <div className={`grounding-note${isNoisyTier ? " noisy" : ""}`}>
              <span className="tier"></span>
              {grounding_note}
            </div>
          ) : (
            <div className="grounding-note" style={{ color: "var(--seal-red)" }}>
              <span className="tier" style={{ background: "var(--seal-red)" }}></span>
              {grounding_note || "No retrieved chunk could ground this claim."}
            </div>
          )}

          {grounding_verified ? (
            <div>
              <span
                className={`stamp ${STAMP_CLASS_BY_VERDICT[verdict] || "review"}`}
                style={{ "--ink": confidence }}
              >
                {STAMP_LABEL_BY_VERDICT[verdict] || verdict}
              </span>
              <div className="confidence-note">
                confidence {confidence?.toFixed(2)}
                {belowThreshold ? " — below 0.90 threshold" : ""}
              </div>
            </div>
          ) : (
            <span className="flag-mark">flagged — unverified</span>
          )}
        </div>
      </div>
    </div>
  );
}
