# src/dicom_agent/tools/dicom_ontology_llm_tool.py
from llm.gemini_client import GeminiClient


PROMPT = """
You are a medical ontology assistant.
Translate the following DICOM metadata into plain English
using anatomy and imaging terminology.


Metadata:
{metadata}
"""


async def explain_metadata(metadata: dict) -> str:
    gemini = GeminiClient()
    prompt = PROMPT.format(metadata=metadata)
    return await gemini.generate(prompt)