import hashlib
from typing import Any, Dict, Optional
from pydantic import BaseModel, model_validator


class IdentityRow(BaseModel):
    """A single row from the SMS click-tracking DataFrame under test."""

    sms_text: str
    country: Optional[str] = None
    location: Optional[str] = None
    inferred_language: Optional[str] = None
    display_type: Optional[str] = None
    click_time: Optional[str] = None   # ISO 8601 string or free-form timestamp
    clicked_url: Optional[str] = None

    # Derived identifier used for output filenames and result tracking.
    # Set explicitly when loading from a DataFrame (e.g. str(df.index[i])),
    # or left blank to auto-generate from a hash of sms_text.
    id: Optional[str] = None

    @model_validator(mode="after")
    def _set_default_id(self) -> "IdentityRow":
        if not self.id:
            digest = hashlib.sha1(self.sms_text.encode()).hexdigest()[:8]
            self.id = f"row_{digest}"
        return self

    def to_agent_input(self) -> str:
        return self.model_dump_json(indent=2, exclude={"id"})


class AttackResult(BaseModel):
    """Full result of a single de-anonymization attack run."""

    identity_row_id: str
    success: bool
    findings: str       # Raw final response from the strategist
    summary: str        # Summarizer's structured report
    iterations_used: int
    total_input_tokens: int
    total_output_tokens: int
    cost_usd: float
    agent_call_counts: Dict[str, int]
