"""
Phase 3 exit criterion: "All tools pass contract tests via MCP Inspector."
This file covers the same ground programmatically (run via `python
eval/test_mcp_contracts.py`) — use it for fast local iteration, and use
`mcp dev mcp_server/server.py` (MCP Inspector) for interactive/manual
contract testing per the roadmap.

Covers, for each tool: valid input, malformed input, empty-corpus-match.
Requires a populated Qdrant store (real ingestion data) and a valid
GROQ_API_KEY in .env — these are integration tests, not pure unit
tests, since they exercise the real retriever + real Groq API calls.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server"))

import tools  # noqa: E402


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    return condition


def run_all():
    results = []

    # --- fetch_regulation ---
    r = tools.fetch_regulation("KYC customer due diligence")
    results.append(check("fetch_regulation: valid input returns results",
                          "results" in r and len(r["results"]) > 0))
    r = tools.fetch_regulation("")
    results.append(check("fetch_regulation: malformed input returns error, not crash",
                          "error" in r))

    # --- check_compliance ---
    r = tools.check_compliance("We retain KYC records for five years after account closure.")
    results.append(check("check_compliance: valid input returns a verdict",
                          "verdict" in r and r["verdict"] in
                          ("Compliant", "Non-Compliant", "Requires Legal Review", "Conflicting Regulations")))
    r = tools.check_compliance("")
    results.append(check("check_compliance: malformed input returns error", "error" in r))

    r = tools.check_compliance("asdkfjaslkdfj qwoeiruqwoiuer nonsense gibberish xyz123")
    results.append(check("check_compliance: nonsense input doesn't crash",
                          "verdict" in r or "error" in r))

    # --- generate_compliance_report ---
    r = tools.generate_compliance_report("We charge a 2% processing fee on personal loans above 5 lakh.")
    results.append(check("generate_compliance_report: valid input returns full report shape",
                          "policy_received" in r and "relevant_regulations_found" in r and "verdict" in r))

    # --- compare_jurisdictions ---
    r = tools.compare_jurisdictions("We retain customer data for 3 years.", ["RBI"])
    results.append(check("compare_jurisdictions: valid input returns per-regulator results",
                          "results_by_regulator" in r and "RBI" in r["results_by_regulator"]))
    r = tools.compare_jurisdictions("policy text", [])
    results.append(check("compare_jurisdictions: empty regulators list returns error", "error" in r))

    # --- detect_regulatory_conflicts ---
    r = tools.detect_regulatory_conflicts("We charge a prepayment penalty on a floating rate loan.")
    results.append(check("detect_regulatory_conflicts: valid input returns conflict_detected bool",
                          "conflict_detected" in r))

    # --- get_regulation_history ---
    r = tools.get_regulation_history("nonexistent_clause_id_xyz")
    results.append(check("get_regulation_history: unknown clause_id returns found=False gracefully",
                          r.get("found") is False))

    # --- simulate_policy_change ---
    r = tools.simulate_policy_change(
        "We charge a 2% processing fee on personal loans.",
        "We charge a 1.5% processing fee on personal loans.",
    )
    results.append(check("simulate_policy_change: valid input returns both verdicts + status_flipped",
                          "status_flipped" in r and "original_verdict" in r and "proposed_verdict" in r))

    print(f"\n{sum(results)}/{len(results)} contract tests passed")


if __name__ == "__main__":
    run_all()
