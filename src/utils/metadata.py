"""
Metadata extraction and normalization tool for agentic AI pipelines.

Features:
- DICOM metadata extraction (via pydicom)
- Generic file metadata fallback
- Text normalization for LLMs / embeddings / RAG
"""

from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    import pydicom
except ImportError:
    pydicom = None

from tools.base import Tool


class MetadataTool(Tool):
    """
    Agent-compatible metadata extraction tool.
    """

    name = "extract_metadata"
    description = (
        "Extract structured metadata from DICOM or generic files and "
        "optionally convert it into LLM-friendly text."
    )

    # ==============================================================
    # Public Agent Methods
    # ==============================================================

    def run(self, files: List[str]) -> Dict[str, Any]:
        """
        Required Tool interface.
        """
        metadata = self.extract_metadata(files)

        return {
            "status": "success",
            "metadata": metadata,
            "count": len(metadata),
            "extracted_at": datetime.utcnow().isoformat()
        }

    def extract_metadata(self, files: List[str]) -> List[Dict[str, Any]]:
        """
        Extract structured metadata from a list of files.
        """
        results = []

        for file_path in files:
            path = Path(file_path)

            if not path.exists():
                results.append({
                    "file": file_path,
                    "error": "File not found"
                })
                continue

            if path.suffix.lower() == ".dcm":
                results.append(self._extract_dicom_metadata(path))
            else:
                results.append(self._extract_generic_metadata(path))

        return results

    def metadata_to_text(self, metadata: List[Dict[str, Any]]) -> List[str]:
        """
        Convert structured metadata into natural language text suitable
        for embeddings, RAG, or LLM reasoning.
        """
        texts = []

        for item in metadata:
            if "error" in item:
                texts.append(
                    f"File {item.get('file')} encountered an error: {item.get('error')}"
                )
                continue

            lines = []

            for key, value in item.items():
                if value is None or key in {"file", "type"}:
                    continue
                lines.append(f"{key.replace('_', ' ')}: {value}")

            summary = f"Metadata for {item.get('file')}:\n" + "; ".join(lines)
            texts.append(summary)

        return texts

    # ==============================================================
    # Internal Helpers
    # ==============================================================

    def _extract_dicom_metadata(self, path: Path) -> Dict[str, Any]:
        if pydicom is None:
            return {
                "file": str(path),
                "type": "dicom",
                "error": "pydicom not installed"
            }

        try:
            ds = pydicom.dcmread(str(path), stop_before_pixels=True)

            return {
                "file": str(path),
                "type": "dicom",
                "patient_id": getattr(ds, "PatientID", None),
                "patient_sex": getattr(ds, "PatientSex", None),
                "patient_birth_date": getattr(ds, "PatientBirthDate", None),
                "study_instance_uid": getattr(ds, "StudyInstanceUID", None),
                "series_instance_uid": getattr(ds, "SeriesInstanceUID", None),
                "study_date": getattr(ds, "StudyDate", None),
                "modality": getattr(ds, "Modality", None),
                "body_part_examined": getattr(ds, "BodyPartExamined", None),
                "manufacturer": getattr(ds, "Manufacturer", None),
                "institution_name": getattr(ds, "InstitutionName", None),
                "rows": getattr(ds, "Rows", None),
                "columns": getattr(ds, "Columns", None)
            }

        except Exception as e:
            return {
                "file": str(path),
                "type": "dicom",
                "error": str(e)
            }

    def _extract_generic_metadata(self, path: Path) -> Dict[str, Any]:
        stat = path.stat()

        return {
            "file": str(path),
            "type": "generic",
            "filename": path.name,
            "extension": path.suffix,
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
