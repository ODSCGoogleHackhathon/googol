"""Gemini-based agent for medical annotation orchestration."""

import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from src.config import settings
from src.schemas import AnnotationOutput
from src.pipelines.annotation_pipeline import AnnotationPipeline
from src.agent.gemini_enhancer import GeminiEnhancer
from src.tools.clinical_chatbot_tool import ClinicalChatbotTool
from DB.agentic_repository import AgenticAnnotationRepo

logger = logging.getLogger(__name__)


class GeminiAnnotationAgent:
    """Agent that orchestrates medical image annotation using Gemini and MedGemma."""

    def __init__(self):
        """Initialize the Gemini agent with bulletproof pipeline."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        genai.configure(api_key=settings.google_api_key)

        # Initialize the Gemini model (for health checks and chat)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.gemini_temperature,
                "max_output_tokens": settings.gemini_max_tokens,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

        # Initialize enhancer for optional features
        self.enhancer = GeminiEnhancer() if settings.enable_gemini_enhancement else None

        # Initialize bulletproof pipeline
        self.pipeline = AnnotationPipeline(enhancer=self.enhancer)

        # Initialize agentic repository for clinical chatbot
        self.agentic_repo = AgenticAnnotationRepo()

        # Initialize clinical chatbot tool (shares the same model instance)
        self.chatbot_tool = ClinicalChatbotTool(model=self.model, repo=self.agentic_repo)

        logger.info(
            f"Gemini agent initialized with bulletproof pipeline "
            f"(model: {settings.gemini_model}, enhancement: {self.enhancer is not None})"
        )

    def annotate_image(
        self,
        image_base64: str,
        user_prompt: Optional[str] = None,
        patient_id: Optional[str] = None,
        enable_enhancement: bool = False,
    ) -> AnnotationOutput:
        """
        Perform bulletproof annotation using the validation pipeline.

        Pipeline: MedGemma → Gemini Validation → Pydantic → (Optional Enhancement)

        Args:
            image_base64: Base64 encoded medical image
            user_prompt: Optional user instructions
            patient_id: Optional patient identifier
            enable_enhancement: Whether to apply Gemini enhancement features

        Returns:
            Validated and structured annotation output
        """
        try:
            logger.info("Starting bulletproof annotation pipeline")

            # Run through the bulletproof pipeline
            annotation, _ = self.pipeline.annotate(
                image_base64=image_base64,
                user_prompt=user_prompt,
                patient_id=patient_id,
                enable_enhancement=enable_enhancement,
                image_path=None,  # Not needed for this method
            )

            logger.info("✓ Annotation pipeline completed successfully")
            return annotation

        except Exception as e:
            logger.error(f"Critical error in annotation pipeline: {e}", exc_info=True)

            # Import here to avoid circular dependency
            from src.schemas import Finding

            # Return a safe error annotation
            return AnnotationOutput(
                patient_id=patient_id or "ERROR",
                findings=[
                    Finding(
                        label="Pipeline Error",
                        location="N/A",
                        severity="Critical",
                    )
                ],
                confidence_score=0.0,
                generated_by="Error",
                additional_notes=f"Critical pipeline error: {str(e)}",
            )


    def chat_with_annotation(self, request_id: int, question: str) -> str:
        """
        Chat with the clinical assistant about a specific annotation.

        This method delegates to the ClinicalChatbotTool to answer questions
        based on grounded annotation data from the two-tier architecture.

        Args:
            request_id: The annotation_request ID to fetch data for
            question: The user's question

        Returns:
            Clinical assistant's response
        """
        return self.chatbot_tool.answer_question(request_id, question)

    def check_health(self) -> Dict[str, bool]:
        """Check if the agent and its components are healthy."""
        health = {"gemini_connected": False, "medgemma_connected": False}

        try:
            # Test Gemini connection
            test_response = self.model.generate_content("test")
            health["gemini_connected"] = bool(test_response)
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")

        # MedGemma is always "connected" for mock implementation
        health["medgemma_connected"] = True

        return health
