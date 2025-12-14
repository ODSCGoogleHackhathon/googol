"""Gemini-powered validation pipeline for MedGemma outputs."""

import logging
import json
from typing import Dict, Any, Optional
import google.generativeai as genai

from src.config import settings

logger = logging.getLogger(__name__)


class GeminiValidator:
    """Validates and structures MedGemma output using Gemini."""

    VALIDATION_SCHEMA = {
        "type": "object",
        "properties": {
            "patient_id": {"type": "string"},
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "location": {"type": "string"},
                        "severity": {"type": "string"},
                    },
                    "required": ["label", "location", "severity"],
                },
            },
            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
            "additional_notes": {"type": "string"},
        },
        "required": ["patient_id", "findings", "confidence_score"],
    }

    def __init__(self):
        """Initialize Gemini validator."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.1,  # Low temp for structured output
                "response_mime_type": "application/json",
            },
        )
        logger.info(f"GeminiValidator initialized with model: {settings.gemini_model}")

    def validate_and_structure(
        self, raw_analysis: str, patient_id: Optional[str] = None, attempt: int = 0
    ) -> Dict[str, Any]:
        """
        Use Gemini to convert raw MedGemma analysis into structured JSON.

        Args:
            raw_analysis: Raw text from MedGemma
            patient_id: Patient identifier
            attempt: Retry attempt number (for prompt adjustment)

        Returns:
            Dictionary ready for AnnotationOutput(**dict)
        """

        if attempt == 0:
            prompt = self._initial_validation_prompt(raw_analysis, patient_id)
        else:
            prompt = self._retry_validation_prompt(raw_analysis, patient_id, attempt)

        try:
            logger.info(f"Gemini validation attempt {attempt + 1}")
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)

            # Post-process: ensure defaults
            result.setdefault("patient_id", patient_id or "UNKNOWN")
            result.setdefault("generated_by", "MedGemma/Gemini")
            result.setdefault("gemini_enhanced", False)

            logger.info(f"✓ Gemini validation successful (attempt {attempt + 1})")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            logger.error(f"Raw response: {response.text}")
            raise
        except Exception as e:
            logger.error(f"Gemini validation error: {e}")
            raise

    def _initial_validation_prompt(
        self, raw_analysis: str, patient_id: Optional[str]
    ) -> str:
        """Generate initial validation prompt."""
        return f"""You are a medical data validator. Convert this MedGemma analysis into structured JSON.

SCHEMA REQUIREMENTS:
{json.dumps(self.VALIDATION_SCHEMA, indent=2)}

RAW MEDGEMMA ANALYSIS:
{raw_analysis}

PATIENT ID: {patient_id or "AUTO-GENERATED"}

INSTRUCTIONS:
1. Extract ALL medical findings mentioned in the analysis
2. For each finding, provide:
   - label: The medical condition or finding (e.g., "Pneumothorax", "Normal", "Fracture")
   - location: Anatomical location (e.g., "Right lung apex", "Left femur", "Overall")
   - severity: Severity level (e.g., "Severe", "Moderate", "Mild", "None")
3. Estimate confidence_score (0.0-1.0) based on:
   - Analysis clarity and detail
   - Presence of hedging language ("possible", "likely")
   - Number of findings identified
4. Include additional_notes with any important context not captured in findings
5. If NO abnormalities found, create ONE finding with:
   - label: "Normal"
   - location: "Overall"
   - severity: "None"

CRITICAL RULES:
- confidence_score MUST be a float between 0.0 and 1.0
- findings array MUST NOT be empty (minimum 1 finding)
- All string fields should be concise but descriptive

Return ONLY valid JSON matching the schema. No markdown, no code blocks, no explanations."""

    def _retry_validation_prompt(
        self, raw_analysis: str, patient_id: Optional[str], attempt: int
    ) -> str:
        """Generate retry validation prompt with stricter instructions."""
        return f"""RETRY VALIDATION (Attempt {attempt + 1}): Previous attempt failed validation.

Be EXTRA careful with data types and required fields:
- confidence_score MUST be a NUMBER (float) between 0.0 and 1.0, NOT a string
- ALL findings MUST have "label", "location", "severity" as STRINGS
- patient_id MUST be a STRING
- findings MUST be an ARRAY with at least 1 item

RAW MEDGEMMA ANALYSIS:
{raw_analysis}

PATIENT ID: {patient_id or "UNKNOWN"}

SCHEMA (follow exactly):
{json.dumps(self.VALIDATION_SCHEMA, indent=2)}

Double-check:
✓ confidence_score is a number, not "0.85" (string)
✓ findings array has at least one item
✓ Each finding has all three required fields

Return ONLY valid JSON. No markdown, no explanations."""
