# RegVerdict — Demo Script & Synthetic Policy Library

## Purpose
A scripted 5-8 minute walkthrough for interviews/presentations, plus a bank of
test policies spanning all verdict types and all 5 tools — so you're never
improvising what to type live.

---

## Demo Script (suggested order, ~6 minutes)

**1. Open with the problem (30 sec)**
"Financial companies have to check every business decision against dense
regulatory text — usually a junior associate manually reading PDFs. RegVerdict
automates that first-pass check, and crucially, it verifies its own citations
before showing you an answer, so it doesn't just sound confident, it proves it."

**2. Workspace — the core loop (90 sec)**
Type: *"We do not charge any pre-payment penalty when a microfinance borrower
repays their loan early."*
→ Point out: the retrieval trace (shows real documents being searched), the
verbatim evidence quote, the stamp landing with confidence, the "grounding
verified" note.

Then type something that should fail: *"We open savings accounts for customers
who want to use a made-up name instead of their real identity."*
→ Point out: Non-Compliant, with the specific clause cited.

**3. The trust mechanism (60 sec) — this is the differentiator, spend real time here**
"Every evidence quote is checked against the source text before you ever see
it. If the model can't produce a real quote, or if its own confidence is below
90%, it downgrades to 'Requires Legal Review' instead of guessing." — type a
deliberately vague/out-of-scope policy (see library below) to show this live.

**4. Policy Diff (45 sec)**
Show a policy flipping from Non-Compliant to Compliant after a proposed change
— demonstrates pre-testing an amendment before filing it.

**5. Compare Jurisdictions (45 sec)**
Run the hard-conflict case (once confirmed) — RBI and GDPR landing on genuinely
different verdicts for the same policy, flagged explicitly rather than silently
picked.

**6. Audit Trail + Word export (30 sec)**
Show the filterable history, export one report to Word, open it live.

**7. Clause Graph (30 sec)**
Pick GDPR (densest cross-referencing), click a node, show the connected clauses.

**8. Close (15 sec)**
"Built end-to-end: custom RAG pipeline with hybrid retrieval, an MCP server
with 7 tools, real authentication, rate limiting, and Dockerized deployment."

---

## Synthetic Policy Library (15 total, spanning verdict types and tools)

### Clearly Compliant
1. "We do not charge any pre-payment penalty when a microfinance borrower repays their loan early."
2. "We retain customer KYC identification records for five years after account closure."
3. "We display our minimum, maximum, and average interest rates prominently on our website."

### Clearly Non-Compliant
4. "We open savings accounts for customers who want to use a made-up name instead of their real identity."
5. "Our recovery agents call defaulting microfinance borrowers at 5:30 a.m. to press for payment."
6. "We link a microfinance loan to a lien on the borrower's savings account as collateral."
7. "We charge a fee for switching an existing loan from BPLR to the Base Rate system."

### Deliberately ambiguous (good for showing honest uncertainty)
8. "We classify a customer as low-risk for KYC purposes based solely on their income level."
9. "We increase a microfinance borrower's effective rate mid-term by adding a new processing fee, without prior notice."
10. "We want to offer a slightly discounted interest rate to employees who refer new personal loan customers."

### Out-of-corpus (shows honest "can't verify" behavior — use this for the trust-mechanism demo moment)
11. "We want to launch a new cryptocurrency staking product for retail customers."

### For Policy Diff (pairs — original / proposed)
12. Original: "We charge a 2% processing fee on personal loans above ₹5 lakh." → Proposed: "We charge a 1.5% processing fee on personal loans above ₹5 lakh."

### For Compare Jurisdictions (candidates for the hard-conflict case — confirm which one actually splits once Groq quota resets)
13. "We retain customer transaction data indefinitely with no deletion policy."
14. "We share customer financial data with a third-party marketing partner without explicit consent."
15. "We retain customer KYC records for exactly 5 years and then permanently delete all copies."

---

## Notes for live demo safety
- Test everything ONE time before presenting live, ideally the same day — Groq's response can vary slightly between runs on ambiguous cases.
- Have a backup screenshot/recording in case of a live network/API hiccup during an actual interview.
- Know your Groq daily quota status before a live demo — a fresh signup/account or a quota check avoids an embarrassing rate-limit mid-presentation.
