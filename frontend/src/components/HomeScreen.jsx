import { useEffect, useState } from "react";
import { API_BASE } from "../api";

// Pre-login landing page. Section structure (hero / benefits / how-it-works
// / closing CTA / footer) is borrowed from the Stitch mockup at
// stich/regverdict_landing_page_midnight_cobalt/code.html for LAYOUT ONLY —
// every color/font/token is this app's own jurisdiction-coded system, and
// every claim below describes what RegVerdict actually does (no invented
// stats, no fake regulators like MiFID II/SEC, no dead nav links to
// Platform/Solutions/Pricing/Careers pages that don't exist).
// onEnter(mode) routes to Login.jsx with "login" or "signup" as its initial tab.
export default function HomeScreen({ onEnter }) {
  const [indexedChunks, setIndexedChunks] = useState(null);

  useEffect(() => {
    // /api/health is deliberately unauthenticated — safe to show a real
    // trust signal before anyone has logged in, instead of inventing a number.
    fetch(`${API_BASE}/api/health`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && setIndexedChunks(data.indexed_chunks))
      .catch(() => {});
  }, []);

  return (
    <div className="landing">
      <div className="landing-nav">
        <div className="wordmark">
          Reg<span>Verdict</span>
        </div>
        <div className="landing-nav-actions">
          <button className="landing-nav-btn ghost" onClick={() => onEnter("login")}>
            Log in
          </button>
          <button className="landing-nav-btn solid" onClick={() => onEnter("signup")}>
            Sign up
          </button>
        </div>
      </div>

      <div className="landing-hero">
        <h1>
          Compliance answers, <span>cited down to the clause.</span>
        </h1>
        <p>
          Describe a business decision in plain language. RegVerdict grounds every verdict in a real,
          quoted clause from your regulatory corpus — color-coded by jurisdiction, so you always know
          exactly which regulator's rule you're looking at.
        </p>
        <div className="landing-cta-row">
          <button className="landing-cta-primary" onClick={() => onEnter("signup")}>
            Start a compliance check
          </button>
        </div>
        {indexedChunks !== null && (
          <div className="landing-trust">{indexedChunks} clauses indexed and searchable right now</div>
        )}

        {/* /api/documents (the real regulator list) requires auth, so it can't
            be fetched pre-login — these codes are the actual two regulators
            currently indexed (confirmed live), shown as an illustration of
            the jurisdiction-coding feature, not fabricated application data. */}
        <div className="landing-jflag-legend">
          <span className="jflag j1">RBI</span>
          <span className="jflag j2">GDPR</span>
          <span className="jflag j3">+</span>
        </div>

        {/* Illustrative preview, not a live/interactive result — the citation
            and quote are a real, verified clause from the indexed corpus
            (rbi_microfinance_fair_practices §6.6), not invented copy. */}
        <div className="landing-preview">
          <div className="bubble-assistant landing-preview-card">
            <div className="assistant-head j1">
              <span className="jflag j1">RBI</span>
              <span className="assistant-tag">rbi_microfinance_fair_practices §6.6</span>
            </div>
            <div className="assistant-body">
              <p className="assistant-summary">Pre-payment penalty on a microfinance loan</p>
              <div className="quote-block">
                <p className="quote-label">Verbatim evidence</p>
                <p className="quote-text">"There shall be no pre-payment penalty on microfinance loans."</p>
              </div>
              <div className="assistant-footer">
                <div className="grounding-note">
                  <span className="dot"></span>Verified verbatim against source clause
                </div>
                <span className="stamp compliant">Compliant</span>
              </div>
            </div>
          </div>
          <p className="landing-preview-caption">A real, verified example — not a live demo</p>
        </div>

        <div className="landing-features">
          <div className="landing-feature">
            <p className="landing-feature-title">Grounded, not guessed</p>
            <p className="landing-feature-body">
              Every verdict quotes the exact source clause it was decided from — no citation without a
              verified, verbatim match against the underlying regulatory text.
            </p>
          </div>
          <div className="landing-feature">
            <p className="landing-feature-title">Jurisdiction-coded</p>
            <p className="landing-feature-body">
              Each regulator gets its own color. Scan a page of citations and know at a glance which
              rule came from where — no re-reading required.
            </p>
          </div>
          <div className="landing-feature">
            <p className="landing-feature-title">Five tools, one corpus</p>
            <p className="landing-feature-body">
              Check a policy, diff a proposed change, compare jurisdictions side by side, audit past
              checks, or explore how clauses cross-reference each other.
            </p>
          </div>
        </div>
      </div>

      <div className="landing-how">
        <h2>From policy to verdict, in one conversation.</h2>
        <div className="landing-how-steps">
          <div className="landing-how-step">
            <div className="landing-how-number">1</div>
            <div>
              <h4>Describe a policy</h4>
              <p>
                Type a business decision or policy in plain language — no document upload, no
                pre-selecting a jurisdiction first.
              </p>
            </div>
          </div>
          <div className="landing-how-step">
            <div className="landing-how-number">2</div>
            <div>
              <h4>We search and verify</h4>
              <p>
                RegVerdict retrieves the most relevant clauses from the indexed corpus and checks the
                evidence quote verbatim against the source text before it's ever shown to you.
              </p>
            </div>
          </div>
          <div className="landing-how-step">
            <div className="landing-how-number">3</div>
            <div>
              <h4>Get a cited verdict</h4>
              <p>
                Compliant, Non-Compliant, Requires Legal Review, or Conflicting Regulations — every
                verdict is tied to the exact clause and jurisdiction it came from.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="landing-cta-section">
        <h2>Ready to see it for yourself?</h2>
        <p>Sign up and run a real compliance check against the indexed RBI and GDPR corpus.</p>
        <button className="landing-cta-primary" onClick={() => onEnter("signup")}>
          Sign up
        </button>
      </div>

      <div className="landing-footer-full">
        <div className="landing-footer-brand">
          <div className="wordmark">
            Reg<span>Verdict</span>
          </div>
          <p>Compliance Copilot — grounded, jurisdiction-coded regulatory answers.</p>
        </div>
        <div className="landing-footer-tools">
          <p className="landing-footer-heading">Tools</p>
          <ul>
            <li>Compliance Workspace</li>
            <li>Policy Diff</li>
            <li>Compare Jurisdictions</li>
            <li>Audit Trail</li>
            <li>Clause Graph</li>
          </ul>
        </div>
      </div>
      <div className="landing-footer">© 2026 RegVerdict — Compliance Copilot</div>
    </div>
  );
}
