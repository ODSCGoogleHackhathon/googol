# tools/metadata_tool.py
from tools.base import Tool


class MetadataTool(Tool):
    name = "extract_metadata"
    description = "Extract metadata from DICOM files"

    def run(self, files: list):

        return {
            "status": "success",
            "metadata": [
                {"file": f, "patient_id": "123", "modality": "CT"}
                for f in files
            ]
        }
