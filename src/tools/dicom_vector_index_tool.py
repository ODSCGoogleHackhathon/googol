# src/dicom_agent/tools/dicom_vector_index_tool.py
import pydicom
from memory.vector_store import VectorStore
from utils.metadata import extract_metadata, metadata_to_text
from tools.dicom_ontology_presenter import present_dicom_using_ontology


async def index_dicom_files_to_vector_db(dicom_files: list[str], store: VectorStore):
    texts, metadatas = [], []
    for f in dicom_files:
        ds = pydicom.dcmread(f, stop_before_pixels=True)
        meta = extract_metadata(ds)
        ont_meta = present_dicom_using_ontology(f)
        texts.append(metadata_to_text(ont_meta))
        metadatas.append({"path": f, **meta})


    await store.add_texts(texts, metadatas)


