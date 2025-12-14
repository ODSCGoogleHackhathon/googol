# src/dicom_agent/agents/coordinator.py
from pipeline.async_ingest import ingest_collection
from tools.dicom_ontology_llm_tool import explain_metadata


async def run_pipeline(collection: str, store):
    await ingest_collection(collection, store)
    results = await store.similarity_search("lung CT")
    return await explain_metadata(results[0].metadata)