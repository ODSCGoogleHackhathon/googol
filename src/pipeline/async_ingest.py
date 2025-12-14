# src/dicom_agent/pipeline/async_ingest.py
import asyncio
from tools.dicom_download_tool import download_dicom_from_tcia
from tools.dicom_vector_index_tool import index_dicom_to_vector_db


async def ingest_collection(collection: str, store):
    dicoms = await asyncio.to_thread(download_dicom_from_tcia, collection)
    await index_dicom_to_vector_db(dicoms, store)