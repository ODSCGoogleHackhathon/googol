# main.py
from tools.image_to_dicom import ImageToDICOMTool


def main():
    tool = ImageToDICOMTool()

    result = tool.run(
        image_path="test_data/input.jpg",
        output_dcm="test_data/output.dcm",
        study_description="AI Generated Image"
    )

if __name__ == "__main__":
    main()