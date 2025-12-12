"""Pydantic schemas for request/response models."""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Finding(BaseModel):
    """Individual medical finding."""
    label: str = Field(..., description="The medical finding label (e.g., 'Pneumothorax')")
    location: str = Field(..., description="Anatomical location of the finding")
    severity: str = Field(..., description="Severity level of the finding")


class AnnotationOutput(BaseModel):
    """Structured annotation output from the LLM."""
    patient_id: str = Field(default="LLM-GEN-001", description="Patient identifier")
    findings: List[Finding] = Field(default_factory=list, description="List of medical findings")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score of the annotation")
    generated_by: str = Field(default="MedGemma/Gemini", description="Models used for generation")
    additional_notes: Optional[str] = Field(None, description="Additional observations or notes")


class AnnotationRequest(BaseModel):
    """Request model for annotation endpoint."""
    image_base64: str = Field(..., description="Base64 encoded medical image")
    user_prompt: Optional[str] = Field(None, description="Optional user instructions")
    patient_id: Optional[str] = Field(None, description="Optional patient identifier")


class AnnotationResponse(BaseModel):
    """Response model for annotation endpoint."""
    success: bool = Field(..., description="Whether the annotation was successful")
    annotation: Optional[AnnotationOutput] = Field(None, description="The generated annotation")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time_seconds: float = Field(..., description="Time taken to process")


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "unhealthy"] = "healthy"
    version: str = "1.0.0"
    gemini_connected: bool = False
    medgemma_connected: bool = False
