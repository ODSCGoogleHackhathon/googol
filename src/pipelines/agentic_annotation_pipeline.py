"""Enhanced agentic annotation pipeline with two-tier DB architecture."""

import logging
from typing import Optional, Tuple, Dict, Any
from pydantic import ValidationError

from src.schemas import AnnotationOutput
from src.tools.medgemma_tool import MedGemmaTool
from src.pipelines.validation_pipeline import GeminiValidator
from src.agent.summary_generator import GeminiSummaryGenerator

logger = logging.getLogger(__name__)


class AgenticAnnotationPipeline:
    """
    Two-tier agentic pipeline with full traceability.

    Flow:
    1. MedGemma → Raw analysis
    2. Gemini Validator → Structured JSON
    3. Pydantic → Validated AnnotationOutput
    4. Save to annotation_request (staging table)
    5. (Optional) Gemini Enhancement
    6. Gemini Summary Generator → Clinical summary
    7. Save to annotation (clean table)

    All intermediate outputs are preserved in annotation_request for debugging.
    """

    def __init__(self, enhancer=None):
        """
        Initialize agentic annotation pipeline.

        Args:
            enhancer: Optional GeminiEnhancer instance
        """
        self.medgemma = MedGemmaTool()
        self.validator = GeminiValidator()
        self.summary_generator = GeminiSummaryGenerator()
        self.enhancer = enhancer  # Optional
        logger.info("AgenticAnnotationPipeline initialized")

    def annotate(
        self,
        image_base64: str,
        set_name: int,
        image_path: str,
        user_prompt: Optional[str] = None,
        patient_id: Optional[int] = None,
        enable_enhancement: bool = False,
    ) -> Tuple[AnnotationOutput, Dict[str, Any], str]:
        """
        Main agentic annotation pipeline.

        Returns:
            Tuple of:
            - AnnotationOutput: Validated annotation
            - Dict: Request data for annotation_request table
            - str: Summary for annotation table
        """

        # Track pipeline metadata
        pipeline_metadata = {
            "medgemma_raw": None,
            "gemini_validated": None,
            "validation_attempt": 0,
            "validation_status": None,
        }

        try:
            # ========================================
            # STEP 1: MedGemma Analysis
            # ========================================
            logger.info(f"[Step 1/6] MedGemma analysis: {image_path}")
            medgemma_raw = self.medgemma.analyze_image(image_base64, user_prompt)
            pipeline_metadata["medgemma_raw"] = medgemma_raw
            logger.debug(f"MedGemma output: {len(medgemma_raw)} chars")

            # ========================================
            # STEP 2: Gemini Validation (with retries)
            # ========================================
            logger.info(f"[Step 2/6] Gemini validation")
            annotation, gemini_validated_dict, validation_meta = self._validated_annotation(
                medgemma_raw, patient_id, max_retries=2
            )

            pipeline_metadata["gemini_validated"] = gemini_validated_dict
            pipeline_metadata["validation_attempt"] = validation_meta["attempt"]
            pipeline_metadata["validation_status"] = validation_meta["status"]

            logger.info(
                f"✓ Validation {validation_meta['status']} (attempt {validation_meta['attempt']})"
            )

            # ========================================
            # STEP 3: Optional Gemini Enhancement
            # ========================================
            if enable_enhancement and self.enhancer:
                logger.info(f"[Step 3/6] Gemini enhancement")
                annotation = self._apply_enhancement(annotation)
            else:
                logger.info(f"[Step 3/6] Skipping enhancement")

            # ========================================
            # STEP 4: Build annotation_request data
            # ========================================
            logger.info(f"[Step 4/6] Building request data")
            request_data = {
                "set_name": set_name,
                "path_url": image_path,
                "patient_id": patient_id,
                "medgemma_raw": pipeline_metadata["medgemma_raw"],
                "gemini_validated": pipeline_metadata["gemini_validated"],
                "validation_attempt": pipeline_metadata["validation_attempt"],
                "validation_status": pipeline_metadata["validation_status"],
                "pydantic_output": annotation.dict(),
                "confidence_score": annotation.confidence_score,
                "gemini_enhanced": annotation.gemini_enhanced,
                "gemini_report": annotation.gemini_report if annotation.gemini_enhanced else None,
                "urgency_level": annotation.urgency_level if annotation.gemini_enhanced else None,
                "clinical_significance": annotation.clinical_significance if annotation.gemini_enhanced else None,
            }

            # ========================================
            # STEP 5: Generate Clinical Summary
            # ========================================
            logger.info(f"[Step 5/6] Generating clinical summary")
            clinical_summary = self.summary_generator.generate_summary(annotation)
            summary_text = clinical_summary.to_desc_string()

            logger.info(f"✓ Summary: {clinical_summary.primary_diagnosis}")

            # ========================================
            # STEP 6: Extract primary label
            # ========================================
            logger.info(f"[Step 6/6] Extracting primary label")
            primary_label = clinical_summary.primary_diagnosis[:20]  # Truncate for VARCHAR2(20)

            logger.info(
                f"✓ Pipeline complete: {len(annotation.findings)} findings, "
                f"confidence={annotation.confidence_score:.2f}, "
                f"label={primary_label}"
            )

            return annotation, request_data, summary_text, primary_label

        except Exception as e:
            logger.error(f"Critical error in agentic pipeline: {e}", exc_info=True)
            raise

    def _validated_annotation(
        self,
        raw_analysis: str,
        patient_id: Optional[int],
        max_retries: int = 2
    ) -> Tuple[AnnotationOutput, Dict[str, Any], Dict[str, Any]]:
        """
        Attempt Gemini validation with retries.

        Returns:
            Tuple of:
            - AnnotationOutput: Validated annotation
            - Dict: Gemini validated dict (for storage)
            - Dict: Metadata (attempt, status)
        """

        last_error = None
        gemini_dict = None

        for attempt in range(max_retries):
            try:
                # Ask Gemini to structure the data
                gemini_dict = self.validator.validate_and_structure(
                    raw_analysis, str(patient_id) if patient_id else None, attempt=attempt
                )

                # Pydantic validation (STRICT)
                annotation = AnnotationOutput(**gemini_dict)

                logger.info(f"✓ Validation successful (attempt {attempt + 1}/{max_retries})")

                return annotation, gemini_dict, {
                    "attempt": attempt + 1,
                    "status": "success"
                }

            except ValidationError as e:
                last_error = e
                logger.warning(
                    f"⚠ Pydantic validation failed (attempt {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    continue
                else:
                    # All retries exhausted, use fallback
                    logger.warning("All Gemini validation attempts failed, using fallback")
                    fallback_annotation = self._fallback_parser(raw_analysis, patient_id, last_error)

                    return fallback_annotation, fallback_annotation.dict(), {
                        "attempt": max_retries,
                        "status": "fallback"
                    }

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in validation (attempt {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    continue
                else:
                    fallback_annotation = self._fallback_parser(raw_analysis, patient_id, last_error)

                    return fallback_annotation, fallback_annotation.dict(), {
                        "attempt": max_retries,
                        "status": "fallback"
                    }

        # Should not reach here
        fallback_annotation = self._fallback_parser(raw_analysis, patient_id, last_error)
        return fallback_annotation, fallback_annotation.dict(), {
            "attempt": max_retries,
            "status": "fallback"
        }

    def _fallback_parser(
        self,
        raw_analysis: str,
        patient_id: Optional[int],
        error: Optional[Exception]
    ) -> AnnotationOutput:
        """Local fallback parser when Gemini validation fails."""

        logger.warning(f"Using fallback parser due to: {error}")

        from src.schemas import Finding

        # Simple keyword detection
        findings = []
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
                findings.append(Finding(label=label, location=location, severity="Unknown"))

        if not findings:
            findings.append(Finding(label="Analysis Incomplete", location="Overall", severity="Unknown"))

        return AnnotationOutput(
            patient_id=str(patient_id) if patient_id else "FALLBACK-UNKNOWN",
            findings=findings,
            confidence_score=0.3,  # Low confidence for fallback
            generated_by="MedGemma/Fallback",
            additional_notes=f"Fallback parser used. Original analysis: {raw_analysis[:500]}",
            gemini_enhanced=False,
        )

    def _apply_enhancement(self, annotation: AnnotationOutput) -> AnnotationOutput:
        """Apply Gemini enhancement features."""

        try:
            logger.info("Applying Gemini enhancements...")

            if hasattr(self.enhancer, "generate_report"):
                annotation.gemini_report = self.enhancer.generate_report(annotation)

            if hasattr(self.enhancer, "assess_urgency"):
                urgency_result = self.enhancer.assess_urgency(annotation)
                annotation.urgency_level = urgency_result.get("urgency")
                annotation.clinical_significance = urgency_result.get("significance")

            annotation.gemini_enhanced = True
            logger.info("✓ Enhancement completed")
            return annotation

        except Exception as e:
            logger.warning(f"Enhancement failed: {e}")
            annotation.gemini_enhanced = False
            return annotation
