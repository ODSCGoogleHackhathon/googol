# src/tools/dicom_download_tool.py

import os
from typing import List
from nbiatoolkit import NBIAClient

DEFAULT_FILE_PATTERN = "%PatientID/%StudyInstanceUID/%SeriesInstanceUID/%InstanceNumber.dcm"

def download_dicom_from_tcia(
    collection: str,
    output_dir: str = "src/data",
    n_parallel: int = 5
) -> List[str]:
    """
    Downloads DICOM series from TCIA into src/data directory.
    Returns list of downloaded DICOM file paths.
    """

    os.makedirs(output_dir, exist_ok=True)

    downloaded_files = []

    with NBIAClient(return_type="dataframe") as client:
        patients = client.getPatients(Collection=collection)
        if patients.empty:
            raise RuntimeError(f"No patients found for collection: {collection}")

        # Pick first patient for demo (agent can choose later)
        patient = patients.iloc[0]

        series_df = client.getSeries(PatientID=patient.PatientId)
        if series_df.empty:
            raise RuntimeError("No series found for patient")

        series_uid = series_df.SeriesInstanceUID.iloc[0]

        client.downloadSeries(
            series_uid,
            output_dir,
            DEFAULT_FILE_PATTERN,
            n_parallel
        )



def file_generator(DOWNLOAD_PATH, TARGET_COLLECTION):
    """
    A generator that yields the full path of every file in a directory 
    and its subdirectories.
    """

    download_dir = os.path.join(DOWNLOAD_PATH)
    print(f"Download Dir: {download_dir}")

    dicom_files = get_all_files_os_walk(download_dir)
    print(f"Successfully Found files: {len(dicom_files)}")

    for f in dicom_files:
        yield f


def get_all_files_os_walk(directory_path):
    file_list = []
    for root, directories, files in os.walk(directory_path):
        for filename in files:
            # Construct the full file path
            full_path = os.path.join(root, filename)
            if full_path.endswith('.dcm'):
                file_list.append(full_path)
    return file_list

def get_all_files_map_os_walk(directory_path):
    file_list = {}
    for root, directories, files in os.walk(directory_path):
        for filename in files:
            # Construct the full file path
            full_path = os.path.join(root, filename)
            if full_path.endswith('.dcm'):
                file_list.update({filename: full_path})
    return file_list

def get_all_files_os_walk_generator(directory_path):
    for root, directories, files in os.walk(directory_path):
        for filename in files:
            # Construct the full file path
            full_path = os.path.join(root, filename)
            if full_path.endswith('.dcm'):
                yield full_path
