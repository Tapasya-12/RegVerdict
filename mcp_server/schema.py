"""
Shared verdict schema — every verdict-producing tool (check_compliance,
generate_compliance_report, compare_jurisdictions, detect_regulatory_conflicts,
simulate_policy_change) returns this shape, per design doc 3.1, so the UI
(Phase 5) can render any of them with the same components.
"""

from enum import Enum
from pydantic import BaseModel, Field


class Verdict(str, Enum):
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    REQUIRES_LEGAL_REVIEW = "Requires Legal Review"
    CONFLICTING_REGULATIONS = "Conflicting Regulations"


class SourceClause(BaseModel):
    document: str
    clause_number: str
    effective_date: str = ""


class VerdictOutput(BaseModel):
    policy_summary: str = Field(..., description="One-line restatement of what the user submitted")
    verdict: Verdict
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_quote: str = Field(..., description="Verbatim span from the retrieved chunk")
    source_clause: SourceClause
    reasoning: str = Field(..., description="Plain-English explanation grounded in evidence_quote")
    recommended_action: str

    # --- Fields populated AFTER the LLM call, not requested from the model ---
    # (grounding.py sets these; the LLM never fills them in itself, since the
    # whole point is to verify the model's own claim independently)
    grounding_verified: bool = False
    grounding_note: str = ""


# Auto-downgrade rule per roadmap risk table:
# "Every verdict below 90% confidence is hard-labeled 'Requires Legal Review'"
CONFIDENCE_DOWNGRADE_THRESHOLD = 0.90
