"""Streamlit frontend for MedAnnotator."""
import streamlit as st
import requests
import base64
import json
from PIL import Image
from io import BytesIO
import time

# Page configuration
st.set_page_config(
    page_title="MedAnnotator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_URL = "http://localhost:8000"


def check_backend_health():
    """Check if the backend is running and healthy."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}


def encode_image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def annotate_image(image_base64: str, user_prompt: str = None, patient_id: str = None):
    """Send annotation request to backend."""
    payload = {
        "image_base64": image_base64,
        "user_prompt": user_prompt,
        "patient_id": patient_id
    }

    try:
        response = requests.post(
            f"{API_URL}/annotate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error calling backend: {e}")
        return None


def main():
    """Main Streamlit application."""
    # Title and description
    st.title("🏥 MedAnnotator")
    st.markdown("""
    **LLM-Assisted Multimodal Medical Image Annotation Tool**

    Upload a medical image (X-ray, CT, MRI) and receive AI-powered structured annotations
    using Gemini and MedGemma models.
    """)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Backend health check
        is_healthy, health_data = check_backend_health()
        if is_healthy:
            st.success("✅ Backend Connected")
            if "gemini_connected" in health_data:
                st.info(f"Gemini: {'✅' if health_data['gemini_connected'] else '❌'}")
                st.info(f"MedGemma: {'✅' if health_data['medgemma_connected'] else '❌'}")
        else:
            st.error("❌ Backend Disconnected")
            st.warning("Please start the backend server: `python -m src.api.main`")

        st.divider()

        st.header("📋 Instructions")
        st.markdown("""
        1. Upload a medical image
        2. (Optional) Add patient ID
        3. (Optional) Add specific instructions
        4. Click "Annotate Image"
        5. Review and edit the results
        """)

        st.divider()

        st.header("ℹ️ About")
        st.markdown("""
        **Team Googol**

        Built for the Agentic AI App Hackathon

        **Technologies:**
        - Gemini 2.0 Flash
        - MedGemma (Mock)
        - FastAPI
        - Streamlit
        """)

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📤 Upload & Configure")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload Medical Image",
            type=["jpg", "jpeg", "png"],
            help="Upload an X-ray, CT scan, or MRI image"
        )

        # Optional inputs
        patient_id = st.text_input(
            "Patient ID (Optional)",
            placeholder="e.g., P-12345",
            help="Optional patient identifier"
        )

        user_prompt = st.text_area(
            "Special Instructions (Optional)",
            placeholder="e.g., Focus on lung fields, Check for pneumothorax",
            help="Optional specific areas to focus on"
        )

        # Display uploaded image
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Medical Image", use_container_width=True)

            # Store in session state
            st.session_state.uploaded_image = image
            st.session_state.image_name = uploaded_file.name

    with col2:
        st.header("📊 Annotation Results")

        if uploaded_file is not None:
            # Annotate button
            if st.button("🔬 Annotate Image", type="primary", use_container_width=True):
                if not is_healthy:
                    st.error("Backend is not running. Please start the server.")
                else:
                    with st.spinner("Analyzing image with AI models..."):
                        # Encode image
                        image_base64 = encode_image_to_base64(st.session_state.uploaded_image)

                        # Call backend
                        start_time = time.time()
                        result = annotate_image(
                            image_base64=image_base64,
                            user_prompt=user_prompt if user_prompt else None,
                            patient_id=patient_id if patient_id else None
                        )
                        elapsed_time = time.time() - start_time

                        if result and result.get("success"):
                            st.session_state.annotation_result = result
                            st.session_state.processing_time = elapsed_time
                            st.success(f"✅ Annotation completed in {elapsed_time:.2f}s")
                        else:
                            error_msg = result.get("error", "Unknown error") if result else "No response"
                            st.error(f"❌ Annotation failed: {error_msg}")

        # Display results if available
        if "annotation_result" in st.session_state:
            result = st.session_state.annotation_result
            annotation = result.get("annotation")

            if annotation:
                # Metrics
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Patient ID", annotation.get("patient_id", "N/A"))
                with col_b:
                    confidence = annotation.get("confidence_score", 0.0)
                    st.metric("Confidence", f"{confidence:.1%}")
                with col_c:
                    num_findings = len(annotation.get("findings", []))
                    st.metric("Findings", num_findings)

                st.divider()

                # Findings
                st.subheader("🔍 Medical Findings")
                findings = annotation.get("findings", [])

                if findings:
                    for idx, finding in enumerate(findings, 1):
                        with st.expander(f"Finding {idx}: {finding.get('label', 'Unknown')}", expanded=True):
                            col_x, col_y = st.columns(2)
                            with col_x:
                                st.write("**Location:**", finding.get("location", "N/A"))
                            with col_y:
                                severity = finding.get("severity", "N/A")
                                severity_color = {
                                    "Severe": "🔴",
                                    "Moderate": "🟠",
                                    "Mild": "🟡",
                                    "None": "🟢",
                                    "Normal": "🟢"
                                }.get(severity, "⚪")
                                st.write(f"**Severity:** {severity_color} {severity}")
                else:
                    st.info("No specific findings detected")

                # Additional notes
                if annotation.get("additional_notes"):
                    st.subheader("📝 Additional Notes")
                    st.info(annotation["additional_notes"])

                # Model info
                st.caption(f"Generated by: {annotation.get('generated_by', 'Unknown')}")

                st.divider()

                # Editable JSON output
                st.subheader("📄 Structured Output (JSON)")
                edited_json = st.text_area(
                    "Edit annotation if needed:",
                    value=json.dumps(annotation, indent=2),
                    height=300
                )

                # Download button
                st.download_button(
                    label="💾 Download Annotation",
                    data=edited_json,
                    file_name=f"annotation_{annotation.get('patient_id', 'unknown')}.json",
                    mime="application/json"
                )

        else:
            st.info("👈 Upload an image and click 'Annotate Image' to see results")


if __name__ == "__main__":
    main()
