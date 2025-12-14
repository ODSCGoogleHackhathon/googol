"""Gemini-powered clinical summary generator with Pydantic validation."""

import logging
import json
from typing import Dict, Any
import google.generativeai as genai

from src.config import settings
from src.schemas import AnnotationOutput
from src.models.summary_models import ClinicalSummary

logger = logging.getLogger(__name__)


class GeminiSummaryGenerator:
    """
    Generates concise clinical summaries from AnnotationOutput for the annotation table.

    Uses Gemini with Pydantic validation to ensure clean, structured summaries.
    """

    def __init__(self):
        """Initialize Gemini model for summary generation."""
        genai.configure(api_key=settings.google_api_key)

        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.2,  # Low temp for consistent summaries
                "max_output_tokens": 1024,
                "response_mime_type": "application/json",
            }
        )

        logger.info("GeminiSummaryGenerator initialized")

    def generate_summary(
        self,
        annotation: AnnotationOutput,
        include_report: bool = True
    ) -> ClinicalSummary:
        """
        Generate a clinical summary from AnnotationOutput.

        Args:
            annotation: The validated AnnotationOutput
            include_report: Whether to include gemini_report in context

        Returns:
            ClinicalSummary (Pydantic validated)
        """

        # Build context from annotation
        findings_list = [
            {
                "label": f.label,
                "location": f.location,
                "severity": f.severity
            }
            for f in annotation.findings
        ]

        context = {
            "findings": findings_list,
            "confidence_score": annotation.confidence_score,
            "additional_notes": annotation.additional_notes,
        }

        # Add enhancement data if available
        if annotation.gemini_enhanced:
            context["urgency_level"] = annotation.urgency_level
            context["clinical_significance"] = annotation.clinical_significance

            if include_report and annotation.gemini_report:
                context["professional_report"] = annotation.gemini_report[:1000]  # Truncate for context

        # Generate prompt
        prompt = self._build_summary_prompt(context)

        try:
            # Call Gemini
            response = self.model.generate_content(prompt)
            summary_dict = json.loads(response.text)

            # Validate with Pydantic
            summary = ClinicalSummary(**summary_dict)

            logger.info(f"✓ Generated summary: {summary.primary_diagnosis}")
            return summary

        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            logger.error(f"Response: {response.text}")
            raise

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise

    def _build_summary_prompt(self, context: Dict[str, Any]) -> str:
        """Build the prompt for summary generation."""

        # Define JSON schema for Gemini
        schema = {
            "type": "object",
            "properties": {
                "primary_diagnosis": {
                    "type": "string",
                    "description": "Primary diagnosis or main finding (concise, e.g., 'Pneumothorax', 'Normal Chest X-ray')"
                },
                "summary": {
                    "type": "string",
                    "maxLength": 3500,
                    "description": "Concise clinical summary in 2-4 sentences. Focus on clinically relevant information."
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                    "description": "List of key findings (max 5). Be specific and concise."
                },
                "recommendations": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Clinical recommendations or next steps. Can be null if none needed."
                },
                "confidence_note": {
                    "type": "string",
                    "maxLength": 200,
                    "description": "Note about confidence level or limitations. Can be null."
                }
            },
            "required": ["primary_diagnosis", "summary", "key_findings"]
        }

        findings_str = json.dumps(context.get("findings", []), indent=2)
        confidence = context.get("confidence_score", 0.0)

        prompt = f"""You are a radiologist creating a concise clinical summary for a medical image annotation.

CONTEXT:
Findings: {findings_str}
Confidence Score: {confidence:.2f}
Additional Notes: {context.get('additional_notes', 'None')}
"""

        # Add enhancement context if available
        if context.get("urgency_level"):
            prompt += f"Urgency: {context['urgency_level']}\n"
        if context.get("clinical_significance"):
            prompt += f"Clinical Significance: {context['clinical_significance']}\n"
        if context.get("professional_report"):
            prompt += f"\nProfessional Report:\n{context['professional_report']}\n"

        prompt += f"""
TASK:
Generate a concise clinical summary following this JSON schema:
{json.dumps(schema, indent=2)}

GUIDELINES:
1. **primary_diagnosis**: Single most important finding (e.g., "Right Lower Lobe Pneumonia", "Normal Study")
2. **summary**: 2-4 sentences covering:
   - What was found
   - Clinical significance
   - Any relevant context
3. **key_findings**: List of specific observations (max 5)
   - Be precise (include location, severity)
   - Prioritize clinically significant findings
4. **recommendations**: Next steps (e.g., "Follow-up CT in 3 months", "No further imaging needed")
   - Leave as null if normal study
5. **confidence_note**: Only if confidence < 0.8 or limitations exist
   - Example: "Limited by motion artifacts"
   - Leave as null if confidence is high

EXAMPLE OUTPUT:
{{
  "primary_diagnosis": "Right Pneumothorax",
  "summary": "Moderate right-sided pneumothorax identified with approximately 30% lung collapse. No mediastinal shift observed. Patient requires immediate clinical correlation and possible intervention.",
  "key_findings": [
    "Right pneumothorax with 30% lung collapse",
    "No mediastinal shift",
    "Clear costophrenic angles bilaterally",
    "No pleural effusion"
  ],
  "recommendations": "Immediate chest tube placement may be required. Clinical correlation with patient symptoms strongly recommended.",
  "confidence_note": null
}}

Return ONLY valid JSON matching the schema. No markdown, no explanations.
"""

        return prompt

    def generate_summary_from_dict(self, annotation_dict: Dict[str, Any]) -> ClinicalSummary:
        """
        Generate summary from annotation dict (for convenience).

        Args:
            annotation_dict: Dict with AnnotationOutput structure

        Returns:
            ClinicalSummary
        """

        # Convert dict to AnnotationOutput
        annotation = AnnotationOutput(**annotation_dict)

        # Generate summary
        return self.generate_summary(annotation)
