"""
MCP server entry point — wires the 7 functions in tools.py as MCP tools
using the FastMCP interface. Run with:

    mcp dev server.py        # opens MCP Inspector for manual contract testing
    python server.py         # runs the server directly (stdio transport)
"""

from mcp.server.fastmcp import FastMCP

import tools

mcp = FastMCP("RegVerdict")


@mcp.tool()
def fetch_regulation(topic: str) -> dict:
    """Given a topic keyword (e.g. 'data retention', 'KYC norms', 'prepayment penalty'),
    retrieves the most relevant regulatory clauses from the indexed corpus."""
    return tools.fetch_regulation(topic)


@mcp.tool()
def check_compliance(policy_text: str) -> dict:
    """Takes a plain-English business decision or internal policy and returns a
    grounded compliance verdict: Compliant / Non-Compliant / Requires Legal Review,
    with a verbatim evidence quote and source clause."""
    return tools.check_compliance(policy_text)


@mcp.tool()
def generate_compliance_report(policy_text: str) -> dict:
    """Produces a full structured compliance report: policy received, relevant
    regulations found, and a grounded compliance verdict."""
    return tools.generate_compliance_report(policy_text)


@mcp.tool()
def compare_jurisdictions(policy_text: str, regulators: list[str]) -> dict:
    """Runs the same policy against multiple regulatory bodies (e.g. ['RBI']) side
    by side, returning a separate grounded verdict per regulator."""
    return tools.compare_jurisdictions(policy_text, regulators)


@mcp.tool()
def detect_regulatory_conflicts(policy_text: str) -> dict:
    """Checks whether applicable regulators disagree on this policy, surfacing the
    conflict explicitly rather than silently resolving to one verdict."""
    return tools.detect_regulatory_conflicts(policy_text)


@mcp.tool()
def get_regulation_history(clause_id: str) -> dict:
    """Returns the amendment lineage (supersedes / superseded_by) of a clause,
    identified by its composite chunk_id or bare clause_number."""
    return tools.get_regulation_history(clause_id)


@mcp.tool()
def simulate_policy_change(original_policy: str, proposed_change: str) -> dict:
    """Diffs two policy versions and reports whether the compliance verdict flips
    between them — lets a team pre-test an amendment before filing it."""
    return tools.simulate_policy_change(original_policy, proposed_change)


if __name__ == "__main__":
    mcp.run()
