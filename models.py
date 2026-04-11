import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class IdentityRow(BaseModel):
    """A pseudonymous identity record from the database under test."""

    id: str
    handle: Optional[str] = None
    location_hint: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    platform_hints: Optional[List[str]] = None
    writing_samples: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_agent_input(self) -> str:
        return self.model_dump_json(indent=2)


class AttackResult(BaseModel):
    """Full result of a single de-anonymization attack run."""

    identity_row_id: str
    success: bool
    findings: str  # Raw final response from the strategist
    summary: str   # Summarizer's structured report
    iterations_used: int
    total_input_tokens: int
    total_output_tokens: int
    cost_usd: float
    agent_call_counts: Dict[str, int]
