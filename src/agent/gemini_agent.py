"""Gemini-based agent for medical annotation orchestration."""

import logging
import json
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from src.config import settings
from src.schemas import AnnotationOutput, Finding
from src.tools.medgemma_tool import MedGemmaTool

logger = logging.getLogger(__name__)


class GeminiAnnotationAgent:
    """Agent that orchestrates medical image annotation using Gemini and MedGemma."""

    def __init__(self):
        """Initialize the Gemini agent with API key and tools."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        genai.configure(api_key=settings.google_api_key)

        # Initialize the Gemini model
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

        # Initialize MedGemma tool
        self.medgemma_tool = MedGemmaTool()

        logger.info(f"Gemini agent initialized with model: {settings.gemini_model}")

    def annotate_image(
        self, image_base64: str, user_prompt: Optional[str] = None, patient_id: Optional[str] = None
    ) -> AnnotationOutput:
        """
        Perform multi-step annotation using ReAct-style reasoning.

        Steps:
        1. Use MedGemma to analyze the medical image
        2. Process MedGemma's output with Gemini
        3. Generate structured JSON annotation

        Args:
            image_base64: Base64 encoded medical image
            user_prompt: Optional user instructions
            patient_id: Optional patient identifier

        Returns:
            Structured annotation output
        """
        try:
            # Step 1: Get MedGemma analysis
            logger.info("Step 1: Analyzing image with MedGemma")
            medgemma_analysis = self.medgemma_tool.analyze_image(
                image_base64=image_base64, prompt=user_prompt
            )
            logger.info(f"MedGemma analysis complete: {len(medgemma_analysis)} chars")

            # Step 2: Parse MedGemma output locally (bypassing Gemini)
            logger.info("Step 2: Parsing MedGemma output locally")
            structured_output = self._create_smart_fallback_annotation(
                medgemma_analysis, patient_id
            )

            return structured_output

        except Exception as e:
            logger.error(f"Error during annotation: {e}", exc_info=True)
            # Return a default error structure
            return AnnotationOutput(
                patient_id=patient_id or "ERROR",
                findings=[],
                confidence_score=0.0,
                generated_by="Error",
                additional_notes=f"Error during processing: {str(e)}",
            )

    def _generate_structured_annotation(
        self, medgemma_analysis: str, user_prompt: Optional[str], patient_id: Optional[str]
    ) -> AnnotationOutput:
        """
        Use Gemini to convert MedGemma's analysis into structured JSON.

        This implements the ReAct pattern:
        - Reason about the medical findings
        - Act by structuring them into a standardized format
        """
        system_prompt = """You are a medical annotation AI assistant. Your task is to convert
medical image analysis results into a structured JSON format.

Given the medical analysis from a specialized model, extract and structure the findings
into the following format:

{
  "patient_id": "string",
  "findings": [
    {
      "label": "string (e.g., 'Pneumothorax', 'Normal', 'Atelectasis')",
      "location": "string (anatomical location)",
      "severity": "string (e.g., 'Mild', 'Moderate', 'Severe', 'None')"
    }
  ],
  "confidence_score": float (0.0 to 1.0),
  "generated_by": "MedGemma/Gemini",
  "additional_notes": "string (any important observations)"
}

Be precise and clinically accurate. Only extract findings that are explicitly mentioned.
If no abnormalities are found, create a finding with label "Normal" and appropriate details."""

        user_message = f"""Medical Analysis Results:

{medgemma_analysis}

Patient ID: {patient_id or 'AUTO-GENERATED'}
User Instructions: {user_prompt or 'None provided'}

Please convert this analysis into the structured JSON format."""

        try:
            # Generate structured output using Gemini
            response = self.model.generate_content(
                [system_prompt, user_message],
                generation_config={"response_mime_type": "application/json"},
            )

            # Parse the JSON response
            json_text = response.text.strip()
            logger.debug(f"Gemini raw response: {json_text}")

            annotation_data = json.loads(json_text)

            # Validate and create AnnotationOutput
            return AnnotationOutput(**annotation_data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini: {e}")
            logger.error(
                f"Raw response: {response.text if 'response' in locals() else 'No response'}"
            )

            # Fallback: try to extract findings manually
            return self._create_fallback_annotation(medgemma_analysis, patient_id)

        except Exception as e:
            logger.error(f"Error generating structured annotation: {e}", exc_info=True)
            return self._create_fallback_annotation(medgemma_analysis, patient_id)

    def _create_smart_fallback_annotation(
        self, analysis: str, patient_id: Optional[str]
    ) -> AnnotationOutput:
        """
        Parse MedGemma output locally without Gemini.
        Returns full analysis in additional_notes.
        """
        import re

        findings = []
        confidence = 0.75

        # Extract confidence if mentioned
        confidence_match = re.search(r"confidence.*?(\d+)%", analysis, re.IGNORECASE)
        if confidence_match:
            confidence = float(confidence_match.group(1)) / 100

        # Extract key findings
        finding_keywords = {
            "pneumothorax": ("Lungs", "Severe"),
            "atelectasis": ("Lungs", "Mild"),
            "consolidation": ("Lungs", "Moderate"),
            "effusion": ("Pleural Space", "Moderate"),
            "cardiomegaly": ("Heart", "Moderate"),
            "fracture": ("Bones", "Severe"),
            "normal": ("Overall", "None"),
            "clear": ("Lungs", "None"),
        }

        analysis_lower = analysis.lower()
        for keyword, (location, severity) in finding_keywords.items():
            if keyword in analysis_lower:
                findings.append(
                    Finding(label=keyword.title(), location=location, severity=severity)
                )

        # If no findings, create generic one
        if not findings:
            findings.append(
                Finding(
                    label="Medical Image Analysis",
                    location="See additional notes",
                    severity="Unknown",
                )
            )

        return AnnotationOutput(
            patient_id=patient_id or "LOCAL-PARSER-001",
            findings=findings,
            confidence_score=confidence,
            generated_by="MedGemma/Local-Parser",
            additional_notes=analysis,  # Full analysis, no truncation
        )

    def _create_fallback_annotation(
        self, analysis: str, patient_id: Optional[str]
    ) -> AnnotationOutput:
        """Create a basic annotation when structured parsing fails."""
        return AnnotationOutput(
            patient_id=patient_id,
            findings=[
                Finding(
                    label="Analysis Available", location="See additional notes", severity="Unknown"
                )
            ],
            confidence_score=0.5,
            generated_by="MedGemma/Gemini-Fallback",
            additional_notes=analysis,  # Full analysis
        )

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
