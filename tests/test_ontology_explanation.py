# tests/test_ontology_explanation.py

import asyncio
from tools.dicom_ontology_llm_tool import explain_metadata

async def test_explanation_guardrails():
    metadata = {
        "Modality": "CT",
        "BodyPart": "CHEST"
    }

    explanation = await explain_metadata(metadata)

    assert "CT" in explanation
    assert "diagnostic" not in explanation.lower()  # guardrail
