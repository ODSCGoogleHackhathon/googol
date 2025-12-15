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
from src.tools.medical_chatbot_tool import MedicalChatbotTool

# Configure logging (console only, no file)
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Global instances
agent: GeminiAnnotationAgent = None
# enhancer: GeminiEnhancer = None
db_repo: AnnotationRepo = None
agentic_repo = None  # Will be set from agent.agentic_repo
agentic_pipeline = None  # Shared pipeline instance to reuse MedGemma model
chatbot: MedicalChatbotTool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global agent, enhancer, db_repo, agentic_repo, agentic_pipeline, chatbot
    logger.info("Starting MedAnnotator API...")
    try:
        agent = GeminiAnnotationAgent()
        logger.info("Gemini agent initialized successfully")

        # if settings.enable_gemini_enhancement:
        #     enhancer = GeminiEnhancer()
        #     logger.info("Gemini enhancer initialized successfully")

        db_repo = AnnotationRepo()
        logger.info("Database repository initialized successfully")

        # Reuse agentic_repo from agent to avoid multiple connections
        agentic_repo = agent.agentic_repo
        logger.info("Agentic repository linked from agent")

        # Initialize agentic pipeline once (reuses MedGemma model across requests)
        from src.pipelines.agentic_annotation_pipeline import AgenticAnnotationPipeline
        agentic_pipeline = AgenticAnnotationPipeline(enhancer=agent.enhancer)
        logger.info("Agentic annotation pipeline initialized (MedGemma model will lazy-load)")

        chatbot = MedicalChatbotTool()
        logger.info("Medical chatbot initialized successfully")
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
    """Load image paths into a dataset (creates placeholder annotation_requests)."""
    if db_repo is None or agentic_repo is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:

        # Get existing annotation_requests to check for duplicates
        existing_requests = agentic_repo.get_unprocessed_requests(set_name=request.data_name)
        existing_paths = {req['path_url'] for req in existing_requests}

        # Also check processed annotations
        existing_annotations = db_repo.get_annotations(request.data_name)
        existing_paths.update({ann[1] for ann in existing_annotations})

        # Filter out duplicates
        new_paths = [path for path in request.data if path not in existing_paths]
        duplicate_count = len(request.data) - len(new_paths)

        # Ensure defaults exist
        db_repo.add_patient(0, "Unknown")

        # Create placeholder annotation_requests (not yet analyzed)
        loaded_count = 0
        for path in new_paths:
            try:
                # Create minimal placeholder request
                agentic_repo.save_annotation_request(
                    set_name=request.data_name,
                    path_url=path,
                    patient_id=0,  # Default patient
                    medgemma_raw="[Pending Analysis]",
                    gemini_validated={"status": "pending"},
                    validation_attempt=0,
                    validation_status="pending",
                    pydantic_output={"patient_id": "0", "findings": [], "confidence_score": 0.0},
                    confidence_score=0.0,
                    gemini_enhanced=False
                )
                loaded_count += 1
            except Exception as e:
                logger.warning(f"Failed to create request for {path}: {e}")

        # Build response message
        message_parts = []
        if loaded_count > 0:
            message_parts.append(f"Loaded {loaded_count} new images to annotation_request queue")
        if duplicate_count > 0:
            message_parts.append(f"{duplicate_count} images already exist (skipped)")
        if not loaded_count and not duplicate_count:
            message_parts.append("No images to load")

        message = ". ".join(message_parts) + "."

        return LoadDataResponse(
            success=True,
            dataset_name=request.data_name,
            images_loaded=loaded_count,
            message=message,
        )
    except Exception as e:
        logger.error(f"Error loading dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/datasets/analyze", response_model=PromptResponse)
def analyze_dataset(request: PromptRequest):
    """Analyze images in dataset with MedGemma using agentic two-tier pipeline."""
    if db_repo is None or agent is None or agentic_repo is None or agentic_pipeline is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:

        # Reset processed flag if force_reanalyze is True
        if request.force_reanalyze:
            if request.flagged:
                # Reset only specific flagged images
                for path in request.flagged:
                    agentic_repo.cursor.execute(
                        "UPDATE annotation_request SET processed = 0 WHERE set_name = ? AND path_url = ?",
                        [request.data_name, path]
                    )
            else:
                # Reset all images in dataset
                agentic_repo.cursor.execute(
                    "UPDATE annotation_request SET processed = 0 WHERE set_name = ?",
                    [request.data_name]
                )
            agentic_repo.connection.commit()
            logger.info(f"Reset processed flag for dataset '{request.data_name}' (force_reanalyze=True)")

        # Get unprocessed annotation_requests to analyze
        if request.flagged:
            # Get specific flagged images from annotation_request table
            all_requests = agentic_repo.get_unprocessed_requests(set_name=request.data_name)
            requests_to_process = [req for req in all_requests if req['path_url'] in request.flagged]
        else:
            # Get all unprocessed requests
            requests_to_process = agentic_repo.get_unprocessed_requests(set_name=request.data_name)

        if not requests_to_process:
            # Check if dataset has any requests at all
            all_requests = agentic_repo.cursor.execute(
                "SELECT COUNT(*) FROM annotation_request WHERE set_name = ?",
                [request.data_name]
            ).fetchone()[0]

            if all_requests == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No images in dataset '{request.data_name}'. Use POST /datasets/load first to add images."
                )
            else:
                # All images already processed
                stats = agentic_repo.get_pipeline_stats(set_name=request.data_name)
                raise HTTPException(
                    status_code=400,
                    detail=f"All images in dataset '{request.data_name}' have already been analyzed. "
                           f"Stats: {stats['processed']}/{stats['total_requests']} processed, "
                           f"avg confidence: {stats['avg_confidence']:.2f}"
                )

        updated_count = 0
        errors = []

        for req in requests_to_process:
            img_path = req['path_url']
            try:
                # Read image
                file_path = Path(img_path)
                if not file_path.exists():
                    errors.append(f"{img_path}: Not found")
                    continue

                with open(file_path, "rb") as f:
                    image_base64 = base64.b64encode(f.read()).decode("utf-8")

                # Use agentic two-tier pipeline
                annotation, request_data, summary_text, primary_label = agentic_pipeline.annotate(
                    image_base64=image_base64,
                    set_name=request.data_name,
                    image_path=img_path,
                    user_prompt=request.prompt,
                    patient_id=0,  # Default patient
                    enable_enhancement=False,  # Make configurable via request if needed
                )

                # Update the existing annotation_request with real data
                request_id = req['id']
                agentic_repo.cursor.execute(
                    """UPDATE annotation_request
                       SET medgemma_raw = ?, gemini_validated = ?, validation_attempt = ?,
                           validation_status = ?, pydantic_output = ?, confidence_score = ?,
                           gemini_enhanced = ?, gemini_report = ?, urgency_level = ?,
                           clinical_significance = ?
                       WHERE id = ?""",
                    (
                        request_data['medgemma_raw'],
                        json.dumps(request_data['gemini_validated']),
                        request_data['validation_attempt'],
                        request_data['validation_status'],
                        json.dumps(request_data['pydantic_output']),
                        request_data['confidence_score'],
                        request_data['gemini_enhanced'],
                        request_data.get('gemini_report'),
                        request_data.get('urgency_level'),
                        request_data.get('clinical_significance'),
                        request_id
                    )
                )
                agentic_repo.connection.commit()

                # Process to annotation table (clean summary)
                agentic_repo.process_request_to_annotation(
                    request_id=request_id,
                    gemini_summary=summary_text,
                    primary_label=primary_label
                )

                logger.info(
                    f"✓ Analyzed {img_path}: {len(annotation.findings)} findings, "
                    f"confidence={annotation.confidence_score:.2f}, label={primary_label}"
                )

                updated_count += 1
            except Exception as e:
                logger.error(f"Error analyzing {img_path}: {e}", exc_info=True)
                errors.append(f"{img_path}: {str(e)}")

        return PromptResponse(
            success=True,
            dataset_name=request.data_name,
            images_analyzed=len(requests_to_process),
            annotations_updated=updated_count,
            message=f"Analyzed {updated_count}/{len(requests_to_process)} images with two-tier pipeline",
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
    """
    AI chatbot for medical image annotation assistance.
    
    Routes to:
    - ClinicalChatbotTool: If request_id is provided (focused Q&A on specific annotation)
    - MedicalChatbotTool: Otherwise (general dataset assistance)
    """
    if chatbot is None or agent is None:
        raise HTTPException(status_code=503, detail="Chatbot or agent not initialized")

    try:
        # Route to ClinicalChatbotTool if request_id is provided
        if request.request_id is not None:
            logger.info(f"Routing to ClinicalChatbotTool for request_id: {request.request_id}")
            response = agent.chat_with_annotation(
                request_id=request.request_id,
                question=request.message
            )
            return ChatResponse(success=True, ai_message=response, error=None)
        
        # Otherwise, use MedicalChatbotTool for general dataset assistance
        logger.info(f"Routing to MedicalChatbotTool for dataset: {request.dataset_name}")
        
        # Use the medical chatbot tool (with global agentic_repo)
        response = chatbot.chat(
            message=request.message,
            dataset_name=request.dataset_name,
            chat_history=request.chat_history,
            db_repo=db_repo,
            agentic_repo=agentic_repo,  # Use global instance
            flagged_paths=request.flagged_paths,
        )

        return ChatResponse(success=True, ai_message=response, error=None)

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
