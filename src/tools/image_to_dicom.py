"""
Agent tool: Convert an image file into a DICOM (Secondary Capture).

Use cases:
- AI-generated images → PACS-compatible DICOM
- Annotation overlays → DICOM
- Synthetic data generation
- Healthcare RAG / imaging pipelines
"""

from typing import Dict, Any
from tools.base import Tool

import datetime
import numpy as np
from PIL import Image
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import (
    ExplicitVRLittleEndian,
    SecondaryCaptureImageStorage,
    generate_uid
)


class ImageToDICOMTool(Tool):
    """
    Agent-compatible image → DICOM conversion tool.
    """

    name = "image_to_dicom"
    description = (
        "Convert a standard image (JPEG/PNG) into a DICOM Secondary Capture file. "
        "Useful for AI annotations, synthetic images, and imaging pipelines."
    )

    # ==========================================================
    # Tool Entry Point
    # ==========================================================

    def run(
        self,
        image_path: str,
        output_dcm: str,
        patient_name: str = "DOE^JOHN",
        patient_id: str = "123456",
        study_description: str = "Image converted to DICOM",
        modality: str = "OT"
    ) -> Dict[str, Any]:
        """
        Convert image to DICOM and save to disk.
        """

        self._image_to_dicom(
            image_path=image_path,
            output_dcm=output_dcm,
            patient_name=patient_name,
            patient_id=patient_id,
            study_description=study_description,
            modality=modality
        )

        return {
            "status": "success",
            "output_dcm": output_dcm,
            "patient_id": patient_id,
            "modality": modality
        }

    # ==========================================================
    # Core Logic
    # ==========================================================

    def _image_to_dicom(
        self,
        image_path: str,
        output_dcm: str,
        patient_name: str,
        patient_id: str,
        study_description: str,
        modality: str
    ):
        # Load image
        img = Image.open(image_path).convert("RGB")
        pixel_array = np.array(img)

        # ---- File Meta ----
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = generate_uid()

        # ---- DICOM Dataset ----
        ds = FileDataset(
            output_dcm,
            {},
            file_meta=file_meta,
            preamble=b"\0" * 128
        )

        # ---- Patient / Study ----
        ds.PatientName = patient_name
        ds.PatientID = patient_id
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID

        ds.Modality = modality
        ds.StudyDescription = study_description
        ds.SeriesDescription = "Image-to-DICOM Conversion"

        now = datetime.datetime.now()
        ds.StudyDate = now.strftime("%Y%m%d")
        ds.StudyTime = now.strftime("%H%M%S")

        # ---- Image Tags ----
        ds.Rows, ds.Columns = pixel_array.shape[:2]
        ds.SamplesPerPixel = 3
        ds.PhotometricInterpretation = "RGB"
        ds.PlanarConfiguration = 0
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0

        ds.PixelData = pixel_array.tobytes()

        # ---- Save ----
        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.save_as(output_dcm)
