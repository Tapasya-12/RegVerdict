import { useRef, useState } from "react";

const EXAMPLE_TEXT =
  "We do not charge any pre-payment penalty when a microfinance borrower repays their loan early.";

export default function IntakeForm({ onSubmit, disabled, indexedClauseCount = 261 }) {
  const [policyText, setPolicyText] = useState(EXAMPLE_TEXT);
  const [ripples, setRipples] = useState([]);
  const btnRef = useRef(null);

  function handleClick(e) {
    const btn = btnRef.current;
    if (btn) {
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height) * 2;
      const id = Date.now();
      const ripple = {
        id,
        size,
        left: e.clientX - rect.left - size / 2,
        top: e.clientY - rect.top - size / 2,
      };
      setRipples((prev) => [...prev, ripple]);
      setTimeout(() => {
        setRipples((prev) => prev.filter((r) => r.id !== id));
      }, 650);
    }

    if (!policyText.trim() || disabled) return;
    onSubmit(policyText.trim());
  }

  return (
    <div className="intake">
      <div className="intake-label">
        <span>Case intake — describe the policy</span>
        <span>RBI · KYC · INTEREST · MFI</span>
      </div>
      <textarea
        className="intake-field"
        placeholder="e.g. We charge a 2% processing fee on personal loans above ₹5 lakh."
        value={policyText}
        onChange={(e) => setPolicyText(e.target.value)}
      />
      <div className="intake-footer">
        <span className="intake-hint">Checked against {indexedClauseCount} indexed clauses</span>
        <button ref={btnRef} className="submit-btn" onClick={handleClick} disabled={disabled}>
          Submit for review
          {ripples.map((r) => (
            <span
              key={r.id}
              className="ripple"
              style={{ width: r.size, height: r.size, left: r.left, top: r.top }}
            />
          ))}
        </button>
      </div>
    </div>
  );
}
