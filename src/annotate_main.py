# main.py
from tools.image_to_dicom_tool import ImageToDICOMTool


def main():
    tool = ImageToDICOMTool()

    result = tool.run(
        image_path="input.jpg",
        output_dcm="output.dcm",
        study_description="AI Generated Image"
    )

if __name__ == "__main__":
    main()