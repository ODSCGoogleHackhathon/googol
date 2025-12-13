"""FastAPI application for medical image annotation."""
import logging
import time
import base64
import json
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.schemas import (
    AnnotationRequest,
    AnnotationResponse,
    HealthResponse,
    LoadDataRequest,
    LoadDataResponse,
    PromptRequest,
    PromptResponse,
    UpdateAnnotationRequest,
    UpdateAnnotationResponse,
    DeleteAnnotationRequest,
    DeleteAnnotationResponse,
    ExportResponse,
)
from src.agent.gemini_agent import GeminiAnnotationAgent
from DB.repository import AnnotationRepo

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global instances
agent: GeminiAnnotationAgent = None
db_repo: AnnotationRepo = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global agent, db_repo
    logger.info("Starting MedAnnotator API...")
    try:
        agent = GeminiAnnotationAgent()
        logger.info("Gemini agent initialized successfully")

        db_repo = AnnotationRepo()
        logger.info("Database repository initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    yield
    logger.info("Shutting down MedAnnotator API...")


# Create FastAPI app
app = FastAPI(
    title="MedAnnotator API",
    description="LLM-Assisted Multimodal Medical Image Annotation Tool",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "MedAnnotator API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if agent is None:
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            gemini_connected=False,
            medgemma_connected=False
        )

    health_status = agent.check_health()

    return HealthResponse(
        status="healthy" if all(health_status.values()) else "unhealthy",
        version="1.0.0",
        gemini_connected=health_status.get("gemini_connected", False),
        medgemma_connected=health_status.get("medgemma_connected", False)
    )


@app.post("/annotate", response_model=AnnotationResponse)
async def annotate_image(request: AnnotationRequest):
    """
    Annotate a medical image using the Gemini + MedGemma pipeline.

    Args:
        request: Annotation request with base64 image and optional prompt

    Returns:
        Structured annotation with findings and metadata
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    start_time = time.time()
    logger.info(f"Received annotation request for patient: {request.patient_id or 'N/A'}")

    try:
        # Perform annotation
        annotation = agent.annotate_image(
            image_base64=request.image_base64,
            user_prompt=request.user_prompt,
            patient_id=request.patient_id
        )

        processing_time = time.time() - start_time
        logger.info(f"Annotation completed in {processing_time:.2f}s")

        return AnnotationResponse(
            success=True,
            annotation=annotation,
            error=None,
            processing_time_seconds=round(processing_time, 2)
        )

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error during annotation: {e}", exc_info=True)

        return AnnotationResponse(
            success=False,
            annotation=None,
            error=str(e),
            processing_time_seconds=round(processing_time, 2)
        )


# ============================================================================
# Dataset Management Endpoints
# ============================================================================


@app.post("/datasets/load", response_model=LoadDataResponse)
def load_dataset(request: LoadDataRequest):
    """Load image paths into a dataset."""
    if db_repo is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        # Prepare annotation data
        annotation_data = [[path, "pending", 0, "Awaiting annotation"] for path in request.data]

        # Ensure defaults exist
        db_repo.add_label("pending")
        db_repo.add_patient(0, "Unknown")

        # Save annotations
        db_repo.save_annotations(request.data_name, annotation_data)

        return LoadDataResponse(
            success=True,
            dataset_name=request.data_name,
            images_loaded=len(request.data),
            message=f"Loaded {len(request.data)} images. Use /datasets/analyze to annotate."
        )
    except Exception as e:
        logger.error(f"Error loading dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/datasets/analyze", response_model=PromptResponse)
def analyze_dataset(request: PromptRequest):
    """Analyze images in dataset with MedGemma."""
    if db_repo is None or agent is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        # Get images to process
        annotations = db_repo.get_annotations(request.data_name, request.flagged)
        images_to_process = [ann[1] for ann in annotations]

        if not images_to_process:
            raise HTTPException(status_code=404, detail=f"No images in dataset '{request.data_name}'")

        updated_count = 0
        errors = []

        for img_path in images_to_process:
            try:
                # Read image
                file_path = Path(img_path)
                if not file_path.exists():
                    errors.append(f"{img_path}: Not found")
                    continue

                with open(file_path, "rb") as f:
                    image_base64 = base64.b64encode(f.read()).decode("utf-8")

                # Analyze with MedGemma
                result = agent.annotate_image(image_base64, request.prompt)

                # Extract label and description
                primary_label = result.findings[0].label if result.findings else "No findings"
                findings_json = json.dumps([f.dict() for f in result.findings])
                desc = f"{findings_json}\n\n{result.additional_notes or ''}"[:500]

                # Update annotation
                db_repo.add_label(primary_label)
                db_repo.update_annotation(request.data_name, img_path, primary_label, desc)

                updated_count += 1
            except Exception as e:
                errors.append(f"{img_path}: {str(e)}")

        return PromptResponse(
            success=True,
            dataset_name=request.data_name,
            images_analyzed=len(images_to_process),
            annotations_updated=updated_count,
            message=f"Analyzed {updated_count}/{len(images_to_process)} images",
            errors=errors if errors else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/annotations", response_model=UpdateAnnotationResponse)
def update_annotation_endpoint(request: UpdateAnnotationRequest):
    """Manually update annotation."""
    if db_repo is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        db_repo.add_label(request.new_label)
        db_repo.update_annotation(request.data_name, request.img, request.new_label, request.new_desc)

        return UpdateAnnotationResponse(
            success=True,
            message="Annotation updated successfully",
            updated=True
        )
    except Exception as e:
        logger.error(f"Error updating annotation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/annotations", response_model=DeleteAnnotationResponse)
def delete_annotation_endpoint(request: DeleteAnnotationRequest):
    """Delete annotation(s)."""
    if db_repo is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        if request.img.lower() == "all":
            # Delete all - get count first
            annotations = db_repo.get_annotations(request.data_name)
            for ann in annotations:
                db_repo.delete_annotation(request.data_name, ann[1])
            deleted = len(annotations)
            message = f"Deleted all {deleted} annotations"
        else:
            db_repo.delete_annotation(request.data_name, request.img)
            deleted = 1
            message = f"Deleted annotation for {request.img}"

        return DeleteAnnotationResponse(
            success=True,
            message=message,
            deleted_count=deleted
        )
    except Exception as e:
        logger.error(f"Error deleting annotation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets/{data_name}/export", response_model=ExportResponse)
def export_dataset(data_name: str):
    """Export dataset annotations as JSON."""
    if db_repo is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        annotations = db_repo.get_annotations(data_name)

        if not annotations:
            raise HTTPException(status_code=404, detail=f"Dataset '{data_name}' not found")

        return ExportResponse(
            dataset_name=data_name,
            total_annotations=len(annotations),
            annotations=[
                {"path": row[1], "label": row[2], "patient_id": row[3], "description": row[4]}
                for row in annotations
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False  # Disabled to prevent reload loop during model loading
    )
