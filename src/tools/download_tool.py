# tools/download_tool.py
from tools.base import Tool
from tools.dicom_download_tool import download_dicom_from_tcia, get_all_files_os_walk_generator

class DownloadTool(Tool):
    name = "download_files"
    description = "Download files from a remote endpoint"
    
    def __init__(self):
        self.TARGET_COLLECTION = 'LGG-18' # A small, publicly accessible collection
        self.TARGET_COLLECTION = 'COVID-19-AR'
        self.TARGET_COLLECTION = 'TCGA-KIRC'
        self.DOWNLOAD_PATH = 'data/tcia_presentation_dat'

    def run(self, url: str, output_dir: str):
        # placeholder logic

        download_dicom_from_tcia(collection=self.TARGET_COLLECTION, output_dir=self.DOWNLOAD_PATH)
        file_map = self.get_all_files_map_os_walk(directory_path=self.DOWNLOAD_PATH)
        return file_map   


    def get_all_files_map_os_walk(self, directory_path):
        file_list = []  

        for f in get_all_files_os_walk_generator(directory_path=self.DOWNLOAD_PATH):
                file_list.append(f)
                
                 
        return {
            "status": "success",
            "files": file_list
        }
