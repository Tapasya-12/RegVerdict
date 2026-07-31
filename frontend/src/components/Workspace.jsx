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

// Converts a session's stored [{role, content, timestamp}, ...] transcript
// (as returned by GET /api/recent_queries) into the {id, role, text} /
// {id, role, result, policyText} shape this component renders. An assistant
// entry's policyText is whatever the immediately preceding user message
// said — that's the same text check_compliance was originally run against,
// needed for "Export as Word" to re-run the report on a restored session.
function hydrateMessages(sessionMessages) {
  return sessionMessages.map((m, i) => {
    if (m.role === "user") {
      return { id: nextMessageId++, role: "user", text: m.content };
    }
    const prev = sessionMessages[i - 1];
    return {
      id: nextMessageId++,
      role: "assistant",
      result: m.content,
      policyText: prev?.role === "user" ? prev.content : null,
    };
  });
}

export default function Workspace({ indexedChunks, regulators, pendingSession, onQuerySubmitted }) {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [policyText, setPolicyText] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState(null);

  const threadRef = useRef(null);
  const lastSessionNonce = useRef(null);

  // Restoring a sidebar entry: load its saved transcript wholesale and adopt
  // its id as the current session, so the NEXT submission appends to this
  // same conversation instead of starting a new sidebar row.
  useEffect(() => {
    if (pendingSession && pendingSession.nonce !== lastSessionNonce.current) {
      lastSessionNonce.current = pendingSession.nonce;
      setSessionId(pendingSession.sessionId);
      setMessages(hydrateMessages(pendingSession.messages));
      setPolicyText("");
    }
  }, [pendingSession]);

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
        body: JSON.stringify({ policy_text: text, session_id: sessionId }),
      });
      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }
      const { session_id, ...result } = await res.json();
      setSessionId(session_id);
      setMessages((prev) => [...prev, { id: nextMessageId++, role: "assistant", result, policyText: text }]);
      onQuerySubmitted?.(text);
    } catch (err) {
      console.error("check_compliance failed:", err);
      setError("Could not reach the compliance engine — check that the backend is running.");
    } finally {
      setReviewing(false);
    }
  }

  function handleTextareaKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
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
            onKeyDown={handleTextareaKeyDown}
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
