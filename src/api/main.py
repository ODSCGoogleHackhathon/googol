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
    GetAnnotationsResponse,
    ChatRequest,
    ChatResponse,
)
from src.agent.gemini_agent import GeminiAnnotationAgent

# from src.agent.gemini_enhancer import GeminiEnhancer
from DB.repository import AnnotationRepo

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Global instances
agent: GeminiAnnotationAgent = None
# enhancer: GeminiEnhancer = None
db_repo: AnnotationRepo = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global agent, enhancer, db_repo
    logger.info("Starting MedAnnotator API...")
    try:
        agent = GeminiAnnotationAgent()
        logger.info("Gemini agent initialized successfully")

        # if settings.enable_gemini_enhancement:
        #     enhancer = GeminiEnhancer()
        #     logger.info("Gemini enhancer initialized successfully")

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
    lifespan=lifespan,
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
    return {"message": "MedAnnotator API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if agent is None:
        return HealthResponse(
            status="unhealthy", version="1.0.0", gemini_connected=False, medgemma_connected=False
        )

    health_status = agent.check_health()

    return HealthResponse(
        status="healthy" if all(health_status.values()) else "unhealthy",
        version="1.0.0",
        gemini_connected=health_status.get("gemini_connected", False),
        medgemma_connected=health_status.get("medgemma_connected", False),
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
        # Perform annotation with MedGemma
        annotation = agent.annotate_image(
            image_base64=request.image_base64,
            user_prompt=request.user_prompt,
            patient_id=request.patient_id,
        )

        # Apply Gemini enhancement if requested and available
        if request.enhance_with_gemini and enhancer is not None:
            logger.info("Applying Gemini enhancement...")
            try:
                # Generate professional report
                annotation.gemini_report = enhancer.generate_report(annotation)

                # Assess urgency
                urgency_result = enhancer.assess_urgency(annotation)
                annotation.urgency_level = urgency_result.get("urgency", "routine")
                annotation.clinical_significance = urgency_result.get("significance", "medium")

                annotation.gemini_enhanced = True
                logger.info("Gemini enhancement completed")
            except Exception as e:
                logger.warning(f"Gemini enhancement failed: {e}")
                annotation.gemini_enhanced = False

        processing_time = time.time() - start_time
        logger.info(f"Annotation completed in {processing_time:.2f}s")

        return AnnotationResponse(
            success=True,
            annotation=annotation,
            error=None,
            processing_time_seconds=round(processing_time, 2),
        )

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error during annotation: {e}", exc_info=True)

        return AnnotationResponse(
            success=False,
            annotation=None,
            error=str(e),
            processing_time_seconds=round(processing_time, 2),
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
        # Get existing annotations to check for duplicates
        existing_annotations = db_repo.get_annotations(request.data_name)
        existing_paths = {ann[1] for ann in existing_annotations}  # path_url is at index 1

        # Filter out duplicates
        new_paths = [path for path in request.data if path not in existing_paths]
        duplicate_count = len(request.data) - len(new_paths)

        # Ensure defaults exist
        db_repo.add_label("pending")
        db_repo.add_patient(0, "Unknown")

        # Save only new annotations
        if new_paths:
            annotation_data = [[path, "pending", 0, "Awaiting annotation"] for path in new_paths]
            db_repo.save_annotations(request.data_name, annotation_data)

        # Build response message
        message_parts = []
        if new_paths:
            message_parts.append(f"Loaded {len(new_paths)} new images")
        if duplicate_count > 0:
            message_parts.append(f"{duplicate_count} images already exist (skipped)")
        if not new_paths and not duplicate_count:
            message_parts.append("No images to load")

        message = ". ".join(message_parts) + "."

        return LoadDataResponse(
            success=True,
            dataset_name=request.data_name,
            images_loaded=len(new_paths),
            message=message,
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
            raise HTTPException(
                status_code=404, detail=f"No images in dataset '{request.data_name}'"
            )

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

                # Use bulletproof pipeline (imports done at top of function)
                annotation, db_data = agent.pipeline.annotate(
                    image_base64=image_base64,
                    user_prompt=request.prompt,
                    patient_id=None,
                    enable_enhancement=False,  # Optional: make this configurable
                    image_path=img_path,
                )

<<<<<<< HEAD
                # Extract label and description
                primary_label = result.findings[0].label if result.findings else "No findings"
                findings_json = json.dumps([f.dict() for f in result.findings])
                desc = f"{findings_json}\n\n{result.additional_notes or ''}"[
                    :4000
                ]  # Match DB limit
=======
                # Update annotation with bulletproof data
                db_repo.add_label(db_data["label"])
                db_repo.add_patient(db_data["patient_id"], "Auto")
                db_repo.update_annotation(
                    request.data_name, img_path, db_data["label"], db_data["desc"]
                )
>>>>>>> cb3f4f7 (add pipeline)

                logger.info(
                    f"✓ Analyzed {img_path}: {len(annotation.findings)} findings, "
                    f"confidence={annotation.confidence_score:.2f}"
                )

                updated_count += 1
            except Exception as e:
                errors.append(f"{img_path}: {str(e)}")

        return PromptResponse(
            success=True,
            dataset_name=request.data_name,
            images_analyzed=len(images_to_process),
            annotations_updated=updated_count,
            message=f"Analyzed {updated_count}/{len(images_to_process)} images",
            errors=errors if errors else None,
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
        db_repo.update_annotation(
            request.data_name, request.img, request.new_label, request.new_desc
        )

        return UpdateAnnotationResponse(
            success=True, message="Annotation updated successfully", updated=True
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

        return DeleteAnnotationResponse(success=True, message=message, deleted_count=deleted)
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
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets/{data_name}/annotations", response_model=GetAnnotationsResponse)
def get_dataset_annotations(data_name: str):
    """Get all annotations for a specific dataset."""
    if db_repo is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        annotations = db_repo.get_annotations(data_name)

        if not annotations:
            return GetAnnotationsResponse(
                dataset_name=data_name, total_annotations=0, annotations=[]
            )

        return GetAnnotationsResponse(
            dataset_name=data_name,
            total_annotations=len(annotations),
            annotations=[
                {"path": row[1], "label": row[2], "patient_id": row[3], "description": row[4]}
                for row in annotations
            ],
        )
    except Exception as e:
        logger.error(f"Error getting annotations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """AI chatbot for dataset labeling assistance."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Build context from dataset if provided
        context = ""
        if request.dataset_name and db_repo is not None:
            annotations = db_repo.get_annotations(request.dataset_name)
            if annotations:
                labels = {}
                for row in annotations:
                    label = row[2]
                    labels[label] = labels.get(label, 0) + 1
                context = f"\n\nDataset '{request.dataset_name}' context:\n"
                context += f"- Total images: {len(annotations)}\n"
                context += f"- Label distribution: {labels}\n"

        # Build conversation history
        history_text = ""
        if request.chat_history:
            for msg in request.chat_history[-5:]:  # Last 5 messages for context
                role = msg.get("name", "user")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"

        # Create prompt for Gemini
        prompt = f"""You are an AI assistant helping with medical image annotation and dataset labeling.

{context}

Conversation history:
{history_text if history_text else '(No previous conversation)'}

User: {request.message}

Provide helpful, concise assistance for dataset labeling tasks. If the user asks to label images, suggest using the analyze endpoint with specific prompts."""

        # Use Gemini agent's model for chat
        import google.generativeai as genai

        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(model_name=settings.gemini_model)
        response = model.generate_content(prompt)

        return ChatResponse(success=True, ai_message=response.text, error=None)

    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        return ChatResponse(success=False, ai_message="", error=f"Chat error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,  # Disabled to prevent reload loop during model loading
    )
