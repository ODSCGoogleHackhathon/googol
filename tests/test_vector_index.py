# tests/test_vector_index.py

import asyncio
from memory.vector_store import VectorStore
from tools.dicom_vector_index_tool import index_dicom_to_vector_db

async def test_indexing_pipeline(tmp_path):
    store = VectorStore(dim=384)

    # fake DICOM metadata text
    texts = ["CT Chest Lung Nodule"]
    metas = [{"Modality": "CT", "BodyPart": "CHEST"}]

    await store.add_texts(texts, metas)

    results = await store.similarity_search("lung CT")

    assert len(results) > 0
    assert "CT" in results[0].metadata["Modality"]
