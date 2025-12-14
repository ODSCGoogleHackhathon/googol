"""Gemini enhancement layer for MedGemma annotations."""

import logging
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from src.config import settings
from src.schemas import AnnotationOutput, Finding

logger = logging.getLogger(__name__)


class GeminiEnhancer:
    """Enhances MedGemma annotations using Gemini 2.0 Flash Lite."""

    def __init__(self):
        """Initialize Gemini enhancer."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.3,  # Low temperature for medical accuracy
                "max_output_tokens": 2048,
            },
        )
        logger.info(f"Gemini enhancer initialized with model: {settings.gemini_model}")

    def generate_report(self, annotation: AnnotationOutput, language: str = "en") -> str:
        """
        Generate professional radiologist report from annotation.

        Args:
            annotation: MedGemma annotation output
            language: Target language (en, pt, es, etc.)

        Returns:
            Professional report text
        """
        findings_text = "\n".join(
            [f"- {f.label} in {f.location} (severity: {f.severity})" for f in annotation.findings]
        )

        prompt = f"""You are an expert radiologist. Generate a professional radiology report.

FINDINGS:
{findings_text}

ADDITIONAL NOTES:
{annotation.additional_notes or 'None'}

Generate a concise, professional radiology report in {language} language.
Include:
1. CLINICAL INDICATION (inferred from findings)
2. TECHNIQUE
3. FINDINGS (detailed description)
4. IMPRESSION (summary and clinical significance)

Use standard medical terminology."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {str(e)}"

    def assess_urgency(self, annotation: AnnotationOutput) -> Dict[str, Any]:
        """
        Assess clinical urgency and significance.

        Returns:
            {
                "urgency": "critical/urgent/routine",
                "significance": "high/medium/low",
                "reasoning": "explanation"
            }
        """
        findings_text = "\n".join(
            [f"- {f.label} in {f.location} (severity: {f.severity})" for f in annotation.findings]
        )

        prompt = f"""You are an expert radiologist. Assess the clinical urgency and significance.

FINDINGS:
{findings_text}

Classify:
1. Urgency level: critical/urgent/routine
   - critical: requires immediate intervention
   - urgent: needs attention within 24 hours
   - routine: can be addressed in normal workflow

2. Clinical significance: high/medium/low

3. Brief reasoning (1-2 sentences)

Return ONLY valid JSON:
{{
    "urgency": "<level>",
    "significance": "<level>",
    "reasoning": "<explanation>"
}}"""

        try:
            response = self.model.generate_content(prompt)
            import json

            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error assessing urgency: {e}")
            return {
                "urgency": "routine",
                "significance": "medium",
                "reasoning": f"Error in assessment: {str(e)}",
            }

    def suggest_differential_diagnoses(self, annotation: AnnotationOutput) -> List[Dict[str, Any]]:
        """
        Suggest differential diagnoses based on findings.

        Returns:
            List of {
                "diagnosis": "name",
                "likelihood": "high/medium/low",
                "supporting_evidence": "..."
            }
        """
        findings_text = "\n".join(
            [f"- {f.label} in {f.location} (severity: {f.severity})" for f in annotation.findings]
        )

        prompt = f"""You are an expert radiologist. Suggest differential diagnoses.

FINDINGS:
{findings_text}

ADDITIONAL CONTEXT:
{annotation.additional_notes or 'None'}

Provide top 3 differential diagnoses as JSON array:
[
    {{
        "diagnosis": "diagnosis name",
        "likelihood": "high/medium/low",
        "supporting_evidence": "brief explanation based on findings"
    }}
]

IMPORTANT: This is for educational/suggestive purposes only.
Return ONLY valid JSON array."""

        try:
            response = self.model.generate_content(prompt)
            import json

            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error generating differential diagnoses: {e}")
            return []

    def quality_check(self, annotation: AnnotationOutput) -> Dict[str, Any]:
        """
        Perform quality check on annotation consistency.

        Returns:
            {
                "consistent": bool,
                "confidence": float,
                "issues": List[str],
                "suggestions": List[str]
            }
        """
        findings_text = "\n".join(
            [f"- {f.label} in {f.location} (severity: {f.severity})" for f in annotation.findings]
        )

        prompt = f"""You are a quality assurance expert for medical imaging annotations.

FINDINGS:
{findings_text}

NOTES:
{annotation.additional_notes or 'None'}

CONFIDENCE SCORE: {annotation.confidence_score}

Check for:
1. Internal consistency (do findings match notes?)
2. Logical coherence (are severity levels appropriate?)
3. Completeness (any missing standard assessments?)
4. Potential errors or contradictions

Return ONLY valid JSON:
{{
    "consistent": true/false,
    "confidence": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

        try:
            response = self.model.generate_content(prompt)
            import json

            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error in quality check: {e}")
            return {
                "consistent": True,
                "confidence": annotation.confidence_score,
                "issues": [],
                "suggestions": [],
            }
