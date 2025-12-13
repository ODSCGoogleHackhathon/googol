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


class LoadDataRequest(BaseModel):
    """Request to load image paths into a dataset."""
    data: List[str] = Field(..., description="List of image file paths")
    data_name: str = Field(..., description="Dataset identifier")
    auto_annotate: bool = Field(default=False, description="Auto-annotate (not implemented)")


class LoadDataResponse(BaseModel):
    """Response from loading dataset."""
    success: bool
    dataset_name: str
    images_loaded: int
    message: str


class PromptRequest(BaseModel):
    """Request to analyze images with a prompt."""
    prompt: str = Field(..., description="Analysis prompt for MedGemma")
    flagged: Optional[List[str]] = Field(default=None, description="Specific images (None = all)")
    data_name: str = Field(..., description="Dataset identifier")


class PromptResponse(BaseModel):
    """Response from prompt analysis."""
    success: bool
    dataset_name: str
    images_analyzed: int
    annotations_updated: int
    message: str
    errors: Optional[List[str]] = None


class UpdateAnnotationRequest(BaseModel):
    """Request to update annotation."""
    img: str = Field(..., description="Image path")
    new_label: str = Field(..., description="Updated label")
    new_desc: str = Field(..., description="Updated description")
    data_name: str = Field(..., description="Dataset identifier")


class UpdateAnnotationResponse(BaseModel):
    """Response from annotation update."""
    success: bool
    message: str
    updated: bool


class DeleteAnnotationRequest(BaseModel):
    """Request to delete annotation(s)."""
    img: str = Field(..., description="Image path or 'all'")
    data_name: str = Field(..., description="Dataset identifier")


class DeleteAnnotationResponse(BaseModel):
    """Response from deletion."""
    success: bool
    message: str
    deleted_count: int


class ExportResponse(BaseModel):
    """Response for dataset export."""
    dataset_name: str
    total_annotations: int
    annotations: List[dict]
