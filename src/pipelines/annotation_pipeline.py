"""Bulletproof annotation pipeline with Gemini validation."""

import logging
from typing import Optional, Tuple
from pydantic import ValidationError

from src.schemas import AnnotationOutput
from src.tools.medgemma_tool import MedGemmaTool
from src.pipelines.validation_pipeline import GeminiValidator
from src.models.db_serializers import AnnotationSerializer

logger = logging.getLogger(__name__)


class AnnotationPipeline:
    """
    Bulletproof pipeline: MedGemma → Gemini Validation → Pydantic → DB

    Responsibilities:
    1. Orchestrate multi-step annotation process
    2. Handle retries and fallbacks
    3. Ensure all data passes Pydantic validation before DB
    """

    def __init__(self, enhancer=None):
        """
        Initialize annotation pipeline.

        Args:
            enhancer: Optional GeminiEnhancer instance for enhancement features
        """
        self.medgemma = MedGemmaTool()
        self.validator = GeminiValidator()
        self.enhancer = enhancer  # Optional
        self.serializer = AnnotationSerializer()
        logger.info("AnnotationPipeline initialized")

    def annotate(
        self,
        image_base64: str,
        user_prompt: Optional[str] = None,
        patient_id: Optional[str] = None,
        enable_enhancement: bool = False,
        image_path: Optional[str] = None,
    ) -> Tuple[AnnotationOutput, dict]:
        """
        Main annotation pipeline.

        Args:
            image_base64: Base64 encoded image
            user_prompt: Optional user instructions
            patient_id: Optional patient identifier
            enable_enhancement: Whether to apply Gemini enhancement
            image_path: Full path to image (for DB storage)

        Returns:
            (annotation, db_data) where db_data is ready for DB insertion
        """

        # Step 1: MedGemma Analysis
        logger.info("Pipeline Step 1: MedGemma analysis")
        raw_analysis = self.medgemma.analyze_image(image_base64, user_prompt)
        logger.debug(f"MedGemma raw output: {raw_analysis[:200]}...")

        # Step 2: Gemini Validation (with retries)
        logger.info("Pipeline Step 2: Gemini validation")
        annotation = self._validated_annotation(raw_analysis, patient_id, max_retries=2)

        # Step 3: Optional Enhancement
        if enable_enhancement and self.enhancer:
            logger.info("Pipeline Step 3: Gemini enhancement")
            annotation = self._apply_enhancement(annotation)
        else:
            logger.info("Pipeline Step 3: Skipping enhancement (disabled or no enhancer)")

        # Step 4: Serialize for DB
        logger.info("Pipeline Step 4: Serialize for database")
        db_data = self.serializer.to_db_format(annotation, image_path or "unknown")

        logger.info(
            f"✓ Pipeline completed successfully: {len(annotation.findings)} findings, "
            f"confidence={annotation.confidence_score:.2f}"
        )

        return annotation, db_data

    def _validated_annotation(
        self, raw_analysis: str, patient_id: Optional[str], max_retries: int = 2
    ) -> AnnotationOutput:
        """
        Attempt Gemini validation with retries.

        Retry strategy:
        1. Gemini structured JSON generation
        2. If validation fails: ask Gemini to fix (retry with stricter prompt)
        3. If still fails: local fallback parser

        Args:
            raw_analysis: Raw text from MedGemma
            patient_id: Patient identifier
            max_retries: Maximum number of retry attempts

        Returns:
            Validated AnnotationOutput instance
        """

        last_error = None

        for attempt in range(max_retries):
            try:
                # Ask Gemini to structure the data
                annotation_dict = self.validator.validate_and_structure(
                    raw_analysis, patient_id, attempt=attempt
                )

                # Pydantic validation (STRICT)
                annotation = AnnotationOutput(**annotation_dict)

                logger.info(
                    f"✓ Validation successful on attempt {attempt + 1}/{max_retries}"
                )
                return annotation

            except ValidationError as e:
                last_error = e
                logger.warning(
                    f"⚠ Pydantic validation failed (attempt {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    # Continue to next retry with stricter prompt
                    logger.info("Retrying with stricter validation prompt...")
                    continue
                else:
                    # All retries exhausted, use fallback
                    logger.warning(
                        "All Gemini validation attempts failed, using local fallback"
                    )
                    return self._fallback_parser(raw_analysis, patient_id, last_error)

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in validation (attempt {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    continue
                else:
                    return self._fallback_parser(raw_analysis, patient_id, last_error)

        # Should not reach here, but just in case
        return self._fallback_parser(raw_analysis, patient_id, last_error)

    def _fallback_parser(
        self, raw_analysis: str, patient_id: Optional[str], error: Optional[Exception]
    ) -> AnnotationOutput:
        """
        Local regex-based parser as last resort.

        Creates a safe, minimal annotation when all validation attempts fail.

        Args:
            raw_analysis: Raw text from MedGemma
            patient_id: Patient identifier
            error: The error that caused fallback

        Returns:
            Safe fallback AnnotationOutput
        """
        logger.warning(f"Using fallback parser due to error: {error}")

        # Import here to avoid circular dependency
        from src.schemas import Finding

        # Try to extract at least some information
        findings = []

        # Simple keyword detection for common findings
        keywords = {
            "pneumothorax": ("Pneumothorax", "Lungs"),
            "fracture": ("Fracture", "Bones"),
            "consolidation": ("Consolidation", "Lungs"),
            "normal": ("Normal", "Overall"),
            "clear": ("Clear", "Lungs"),
        }

        raw_lower = raw_analysis.lower()
        for keyword, (label, location) in keywords.items():
            if keyword in raw_lower:
                findings.append(
                    Finding(label=label, location=location, severity="Unknown")
                )

        # If no findings detected, create a default
        if not findings:
            findings.append(
                Finding(
                    label="Analysis Incomplete",
                    location="Overall",
                    severity="Unknown",
                )
            )

        # Create safe annotation with low confidence
        return AnnotationOutput(
            patient_id=patient_id or "FALLBACK-UNKNOWN",
            findings=findings,
            confidence_score=0.3,  # Low confidence for fallback
            generated_by="MedGemma/Fallback",
            additional_notes=f"Fallback parser used. Original analysis: {raw_analysis[:500]}",
            gemini_enhanced=False,
        )

    def _apply_enhancement(self, annotation: AnnotationOutput) -> AnnotationOutput:
        """
        Apply Gemini enhancement features.

        Args:
            annotation: Base annotation to enhance

        Returns:
            Enhanced annotation (or original if enhancement fails)
        """
        try:
            logger.info("Applying Gemini enhancements...")

            # Generate report
            if hasattr(self.enhancer, "generate_report"):
                annotation.gemini_report = self.enhancer.generate_report(annotation)
                logger.debug("✓ Generated Gemini report")

            # Assess urgency
            if hasattr(self.enhancer, "assess_urgency"):
                urgency_result = self.enhancer.assess_urgency(annotation)
                annotation.urgency_level = urgency_result.get("urgency")
                annotation.clinical_significance = urgency_result.get("significance")
                logger.debug(
                    f"✓ Assessed urgency: {annotation.urgency_level}, "
                    f"significance: {annotation.clinical_significance}"
                )

            annotation.gemini_enhanced = True
            logger.info("✓ Enhancement completed successfully")
            return annotation

        except Exception as e:
            logger.warning(f"Enhancement failed: {e}, continuing with base annotation")
            annotation.gemini_enhanced = False
            return annotation
