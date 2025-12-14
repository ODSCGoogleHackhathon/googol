"""Database serialization utilities with smart truncation."""

import json
import logging
from typing import Dict, Any
from src.schemas import AnnotationOutput

logger = logging.getLogger(__name__)


class AnnotationSerializer:
    """Handles serialization of AnnotationOutput to DB format."""

    MAX_DESC_LENGTH = 3900  # Safety margin below 4000

    def to_db_format(
        self, annotation: AnnotationOutput, image_path: str
    ) -> Dict[str, Any]:
        """
        Convert AnnotationOutput to database format.

        Args:
            annotation: Validated AnnotationOutput from pipeline
            image_path: Full image path

        Returns:
            {
                'path': str,       # For path_url field
                'label': str,      # Primary label
                'patient_id': int,
                'desc': str        # JSON string with all metadata
            }
        """

        # Extract primary label
        primary_label = (
            annotation.findings[0].label if annotation.findings else "No findings"
        )

        # Serialize to comprehensive JSON
        desc_data = {
            "findings": [f.dict() for f in annotation.findings],
            "confidence_score": annotation.confidence_score,
            "generated_by": annotation.generated_by,
            "additional_notes": annotation.additional_notes,
        }

        # Add Gemini metadata if enhanced
        if annotation.gemini_enhanced:
            gemini_meta = {}
            if annotation.gemini_report:
                gemini_meta["report"] = annotation.gemini_report
            if annotation.urgency_level:
                gemini_meta["urgency"] = annotation.urgency_level
            if annotation.clinical_significance:
                gemini_meta["significance"] = annotation.clinical_significance

            if gemini_meta:
                desc_data["gemini_metadata"] = gemini_meta

        # Serialize with truncation
        desc_json = self._truncate_json(desc_data)

        # Convert patient_id to int (or use default)
        try:
            patient_id_int = int(annotation.patient_id)
        except (ValueError, TypeError):
            patient_id_int = 0  # Default patient

        return {
            "path": image_path,
            "label": primary_label[:20],  # Truncate to VARCHAR2(20)
            "patient_id": patient_id_int,
            "desc": desc_json,
        }

    def _truncate_json(self, data: dict) -> str:
        """
        Smart truncation preserving critical fields.

        Priority: findings > confidence_score > gemini_metadata > additional_notes
        """
        json_str = json.dumps(data, ensure_ascii=False, indent=None)

        if len(json_str) <= self.MAX_DESC_LENGTH:
            return json_str

        logger.warning(
            f"Description too long ({len(json_str)} chars), truncating to {self.MAX_DESC_LENGTH}"
        )

        # Strategy 1: Truncate additional_notes
        if "additional_notes" in data and data["additional_notes"]:
            original_notes = data["additional_notes"]
            if len(original_notes) > 500:
                data["additional_notes"] = original_notes[:500] + "...[truncated]"
                json_str = json.dumps(data, ensure_ascii=False, indent=None)
                logger.info(f"Truncated additional_notes: {len(json_str)} chars")

        # Strategy 2: Truncate Gemini report if present
        if len(json_str) > self.MAX_DESC_LENGTH:
            if "gemini_metadata" in data and "report" in data["gemini_metadata"]:
                original_report = data["gemini_metadata"]["report"]
                if len(original_report) > 800:
                    data["gemini_metadata"]["report"] = (
                        original_report[:800] + "...[truncated]"
                    )
                    json_str = json.dumps(data, ensure_ascii=False, indent=None)
                    logger.info(f"Truncated gemini_report: {len(json_str)} chars")

        # Strategy 3: Final hard truncation if needed
        if len(json_str) > self.MAX_DESC_LENGTH:
            logger.warning(
                f"Hard truncation required: {len(json_str)} -> {self.MAX_DESC_LENGTH}"
            )
            json_str = json_str[: self.MAX_DESC_LENGTH]

        return json_str

    def from_db_format(self, db_row: tuple) -> Dict[str, Any]:
        """
        Deserialize database row back to structured format.

        Args:
            db_row: (set_name, path_url, label, patient_id, desc)

        Returns:
            Dictionary with parsed desc JSON
        """
        set_name, path_url, label, patient_id, desc_json = db_row

        try:
            desc_data = json.loads(desc_json)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse desc JSON for {path_url}")
            desc_data = {"error": "Failed to parse stored JSON", "raw": desc_json}

        return {
            "set_name": set_name,
            "path": path_url,
            "label": label,
            "patient_id": patient_id,
            "desc_data": desc_data,
        }
