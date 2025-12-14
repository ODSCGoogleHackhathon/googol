# src/tools/dicom_ontology_presenter.py

import pydicom
from typing import Dict, Any

ONTOLOGY_LOOKUP = {
    "CT": "a standard X-ray-based scan (CT scan).",
    "MR": "a scan using magnetic fields (MRI).",
    "DX": "a digital X-ray image.",
    "CHEST": "the chest and lungs.",
    "ABDOMEN": "the abdominal cavity.",
    "HEAD": "the head and brain.",
    "T1": "an MRI sequence highlighting fatty tissue.",
}

def translate(term: str) -> str:
    if term in ONTOLOGY_LOOKUP:
        return ONTOLOGY_LOOKUP[term]
    for k, v in ONTOLOGY_LOOKUP.items():
        if k in term:
            return v
    return f"{term} (a specialized medical term)"

def extract_metadata(ds: pydicom.Dataset) -> Dict[str, Any]:
    return {
        "PatientID": getattr(ds, "PatientID", "N/A"),
        "StudyDate": getattr(ds, "StudyDate", "N/A"),
        "Modality": getattr(ds, "Modality", "N/A"),
        "BodyPart": getattr(ds, "BodyPartExamined", "N/A"),
        "Protocol": getattr(ds, "ProtocolName",
                            getattr(ds, "SeriesDescription", "Generic Scan"))
    }

def present_dicom_using_ontology(dicom_file: str) -> str:
    ds = pydicom.dcmread(dicom_file, stop_before_pixels=True)
    meta = extract_metadata(ds)

    return f"""
--- DICOM Image Explanation ---

Image Type:
• {meta['Modality']} — {translate(meta['Modality'])}

Anatomy:
• {meta['BodyPart']} — {translate(meta['BodyPart'])}

Scan Technique:
• {meta['Protocol']} — {translate(meta['Protocol'])}

Study Date:
• {meta['StudyDate']}

Patient Context:
• Internal ID: {meta['PatientID']}

This description translates technical imaging metadata into
human-readable clinical context.
""".strip()
