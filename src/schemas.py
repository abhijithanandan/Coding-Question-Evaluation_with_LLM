from __future__ import annotations
from pydantic import BaseModel, Field


class CodingEvaluation(BaseModel):
    """Schema for coding question evaluation results.

    - score: numeric score (non-negative)
    - breakdown: concise explanation string
    """

    score: float = Field(..., ge=0.0, description="Awarded score for the submission.")
    breakdown: str = Field(
        ...,
        min_length=1,
        description="Concise explanation of how the score was determined.",
    )
