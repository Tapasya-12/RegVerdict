// tools.check_compliance() (and simulate_policy_change()'s two halves) nest
// document/clause under source_clause (and return it as null for the
// empty-corpus-match case); ExhibitCard's props are flat, per the design
// doc. This is the one seam between the two shapes, shared by every view
// that renders a check_compliance-shaped result as an ExhibitCard
// (App.jsx's Workspace thread, PolicyDiffView's Before/After pair).
//
// Deliberately no placeholder fallback for document_name/clause_number here:
// ExhibitCard itself decides how to render the true no-match case ("no
// matching clause found") vs a real-but-ungrounded citation, and conflating
// the two by filling in a fallback string here would erase that distinction.
export function toExhibitProps(result) {
  const source = result.source_clause || null;
  return {
    document_name: source?.document,
    clause_number: source?.clause_number,
    policy_summary: result.policy_summary,
    evidence_quote: result.evidence_quote,
    reasoning: result.reasoning,
    grounding_verified: result.grounding_verified,
    grounding_note: result.grounding_note,
    verdict: result.verdict,
    confidence: result.confidence,
  };
}
