import { useRef, useState } from "react";
import RippleButton from "./RippleButton";

const EXAMPLE_TEXT =
  "We do not charge any pre-payment penalty when a microfinance borrower repays their loan early.";

export default function IntakeForm({ onSubmit, disabled, indexedClauseCount = 261 }) {
  const [policyText, setPolicyText] = useState(EXAMPLE_TEXT);
  const textareaRef = useRef(null);

  async function handleClick() {
    const text = policyText.trim();
    if (!text || disabled) return;

    const succeeded = await onSubmit(text);
    if (succeeded) {
      setPolicyText("");
      textareaRef.current?.focus();
    }
  }

  return (
    <div className="intake">
      <div className="intake-label">
        <span>Case intake — describe the policy</span>
        <span>RBI · KYC · INTEREST · MFI</span>
      </div>
      <textarea
        ref={textareaRef}
        className="intake-field"
        placeholder="e.g. We charge a 2% processing fee on personal loans above ₹5 lakh."
        value={policyText}
        onChange={(e) => setPolicyText(e.target.value)}
      />
      <div className="intake-footer">
        <span className="intake-hint">Checked against {indexedClauseCount} indexed clauses</span>
        <RippleButton className="submit-btn" onClick={handleClick} disabled={disabled}>
          Submit for review
        </RippleButton>
      </div>
    </div>
  );
}
