# src/dicom_agent/tools/dicom_vector_index_tool.py
import pydicom
from memory.vector_store import VectorStore
from utils.metadata import MetadataTool
from tools.dicom_ontology_presenter import present_dicom_using_ontology


async def index_dicom_files_to_vector_db(dicom_files: list[str], store: VectorStore):
    texts, metadatas = [], []
    meta_tool = MetadataTool()
    for f in dicom_files:
        ds = pydicom.dcmread(f, stop_before_pixels=True)
        meta = meta_tool.extract_metadata(ds)
        ont_meta = present_dicom_using_ontology(f)
        texts.append(meta_tool.metadata_to_text(ont_meta))
        metadatas.append({"path": f, **meta})


    await store.add_texts(texts, metadatas)


