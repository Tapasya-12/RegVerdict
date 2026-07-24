import { useEffect, useRef, useState } from "react";
import AssistantBubble from "./AssistantBubble";
import RetrievalTrace from "./RetrievalTrace";
import { apiFetch } from "../api";

const CHIPS = [
  {
    label: "Prepayment penalty on floating rate loan?",
    text: "Can we charge a prepayment penalty on a floating rate loan?",
  },
  {
    label: "KYC record retention period?",
    text: "How long must we retain customer KYC records after account closure?",
  },
  {
    label: "Recovery call timing rules?",
    text: "Can we call a defaulting borrower before 9am to collect payment?",
  },
];

let nextMessageId = 0;

export default function Workspace({ indexedChunks, regulators, pendingFill, onQuerySubmitted }) {
  const [messages, setMessages] = useState([]);
  const [policyText, setPolicyText] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState(null);

  const threadRef = useRef(null);
  const lastFillNonce = useRef(null);

  useEffect(() => {
    if (pendingFill && pendingFill.nonce !== lastFillNonce.current) {
      lastFillNonce.current = pendingFill.nonce;
      setPolicyText(pendingFill.text);
    }
  }, [pendingFill]);

  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, reviewing]);

  async function handleSend() {
    const text = policyText.trim();
    if (!text || reviewing) return;

    setMessages((prev) => [...prev, { id: nextMessageId++, role: "user", text }]);
    setPolicyText("");
    setReviewing(true);
    setError(null);

    try {
      const res = await apiFetch("/api/check_compliance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ policy_text: text }),
      });
      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }
      const result = await res.json();
      setMessages((prev) => [...prev, { id: nextMessageId++, role: "assistant", result, policyText: text }]);
      onQuerySubmitted?.(text);
    } catch (err) {
      console.error("check_compliance failed:", err);
      setError("Could not reach the compliance engine — check that the backend is running.");
    } finally {
      setReviewing(false);
    }
  }

  return (
    <>
      <div className="chat-header">
        <div>
          <div className="chat-header-title">Compliance Workspace</div>
          <div className="chat-header-sub">Describe a policy — every answer cites its exact source clause.</div>
        </div>
        <div className="corpus-pill">{regulators.length ? regulators.join(" · ") : "…"}</div>
      </div>

      <div className="chat-thread" ref={threadRef}>
        {messages.map((msg) =>
          msg.role === "user" ? (
            <div className="msg-row user" key={msg.id}>
              <div className="bubble-user">{msg.text}</div>
            </div>
          ) : (
            <div className="msg-row assistant" key={msg.id}>
              <AssistantBubble result={msg.result} policyText={msg.policyText} />
            </div>
          )
        )}

        <RetrievalTrace active={reviewing} />

        {error && (
          <p className="input-hint" style={{ color: "var(--seal-red)" }}>
            {error}
          </p>
        )}
      </div>

      <div className="input-bar-wrap">
        <div className="chip-row">
          {CHIPS.map((chip) => (
            <button key={chip.label} className="chip" onClick={() => setPolicyText(chip.text)}>
              {chip.label}
            </button>
          ))}
        </div>
        <div className="input-bar">
          <textarea
            rows="1"
            placeholder="Describe a business decision or policy…"
            value={policyText}
            onChange={(e) => setPolicyText(e.target.value)}
            disabled={reviewing}
          />
          <button className="send-btn" onClick={handleSend} disabled={reviewing || !policyText.trim()}>
            Send
          </button>
        </div>
        <div className="input-hint">
          RegVerdict checks every citation against the source text before showing you a verdict.
        </div>
      </div>
    </>
  );
}
