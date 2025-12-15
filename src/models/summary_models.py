"""Pydantic models for Gemini summary generation."""

from pydantic import BaseModel, Field
from typing import List, Optional


class ClinicalSummary(BaseModel):
    """
    Gemini-generated clinical summary for annotation table.

    This is what goes into the annotation.desc field (max 4000 chars).
    """

    primary_diagnosis: str = Field(..., description="Primary diagnosis or finding")

    summary: str = Field(
        ...,
        max_length=3500,
        description="Concise clinical summary (2-4 sentences max)"
    )

    key_findings: List[str] = Field(
        ...,
        max_items=5,
        description="List of key findings (max 5)"
    )

    recommendations: Optional[str] = Field(
        None,
        max_length=500,
        description="Clinical recommendations or next steps"
    )

    confidence_note: Optional[str] = Field(
        None,
        max_length=200,
        description="Note about confidence level or limitations"
    )

    def to_desc_string(self) -> str:
        """
        Convert to formatted string for annotation.desc field.

        Format:
        PRIMARY DIAGNOSIS: ...

        SUMMARY:
        ...

        KEY FINDINGS:
        - ...
        - ...

        RECOMMENDATIONS:
        ...

        CONFIDENCE NOTE:
        ...
        """

        parts = []

        # Primary diagnosis
        parts.append(f"PRIMARY DIAGNOSIS: {self.primary_diagnosis}")
        parts.append("")

        # Summary
        parts.append("SUMMARY:")
        parts.append(self.summary)
        parts.append("")

        # Key findings
        if self.key_findings:
            parts.append("KEY FINDINGS:")
            for finding in self.key_findings:
                parts.append(f"- {finding}")
            parts.append("")

        # Recommendations
        if self.recommendations:
            parts.append("RECOMMENDATIONS:")
            parts.append(self.recommendations)
            parts.append("")

        # Confidence note
        if self.confidence_note:
            parts.append("CONFIDENCE NOTE:")
            parts.append(self.confidence_note)

        return "\n".join(parts)


class SummaryGenerationRequest(BaseModel):
    """Request for Gemini to generate a clinical summary."""

    findings: List[dict] = Field(..., description="List of Finding dicts")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    additional_notes: Optional[str] = None
    urgency_level: Optional[str] = None
    clinical_significance: Optional[str] = None
    gemini_report: Optional[str] = None
