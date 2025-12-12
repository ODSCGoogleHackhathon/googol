"""FastAPI application for medical image annotation."""
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.schemas import (
    AnnotationRequest,
    AnnotationResponse,
    HealthResponse
)
from src.agent.gemini_agent import GeminiAnnotationAgent

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

# Global agent instance
agent: GeminiAnnotationAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global agent
    logger.info("Starting MedAnnotator API...")
    try:
        agent = GeminiAnnotationAgent()
        logger.info("Gemini agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )
