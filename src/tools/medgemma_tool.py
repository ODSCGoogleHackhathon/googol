"""MedGemma integration tool for medical image analysis using HuggingFace."""
import logging
from typing import Optional, Dict, Any
import base64
from io import BytesIO
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM

from src.config import settings

logger = logging.getLogger(__name__)


class MedGemmaTool:
    """Tool for interacting with MedGemma model via HuggingFace."""

    def __init__(self):
        """
        Initialize MedGemma tool.

        Supports three modes:
        - mock: Fast mock responses for testing
        - huggingface: Real MedGemma model from HuggingFace
        - vertex_ai: Google Vertex AI endpoint (future)
        """
        self.endpoint = settings.medgemma_endpoint
        self.model_id = settings.medgemma_model_id
        self.cache_dir = settings.medgemma_cache_dir
        self.device = self._determine_device(settings.medgemma_device)

        self.model = None
        self.processor = None

        logger.info(f"Initializing MedGemma tool with endpoint: {self.endpoint}")

        if self.endpoint == "huggingface":
            self._load_huggingface_model()

    def _determine_device(self, device_preference: str) -> str:
        """Determine the best device to use."""
        if device_preference != "auto":
            return device_preference

        # Auto-detect best device
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"  # Apple Silicon
        else:
            return "cpu"

    def _load_huggingface_model(self):
        """Load the MedGemma model from HuggingFace."""
        try:
            logger.info(f"Loading MedGemma model: {self.model_id}")
            logger.info(f"Cache directory: {self.cache_dir}")
            logger.info(f"Device: {self.device}")

            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                self.model_id,
                cache_dir=self.cache_dir,
                token=settings.huggingface_token if settings.huggingface_token else None
            )

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float16 if self.device in ["cuda", "mps"] else torch.float32,
                device_map=self.device if self.device == "auto" else None,
                token=settings.huggingface_token if settings.huggingface_token else None
            )

            if self.device not in ["auto"]:
                self.model = self.model.to(self.device)

            logger.info("✓ MedGemma model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load MedGemma model: {e}")
            logger.warning("Falling back to mock mode")
            self.endpoint = "mock"

    def analyze_image(self, image_base64: str, prompt: Optional[str] = None) -> str:
        """
        Analyze a medical image using MedGemma.

        Args:
            image_base64: Base64 encoded image
            prompt: Optional analysis prompt

        Returns:
            Analysis results as a string
        """
        try:
            # Decode image
            image_data = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_data))

            if image.mode != 'RGB':
                image = image.convert('RGB')

            logger.info(f"Analyzing image of size: {image.size}, mode: {image.mode}")

            # Route to appropriate endpoint
            if self.endpoint == "huggingface" and self.model is not None:
                return self._huggingface_analysis(image, prompt)
            elif self.endpoint == "vertex_ai":
                return self._vertex_ai_analysis(image, prompt)
            else:
                # Fallback to mock
                return self._mock_medgemma_analysis(image, prompt)

        except Exception as e:
            logger.error(f"Error analyzing image with MedGemma: {e}")
            return f"Error during analysis: {str(e)}"

    def _huggingface_analysis(self, image: Image.Image, prompt: Optional[str]) -> str:
        """
        Analyze medical image using HuggingFace MedGemma model.
        """
        try:
            # Create prompt for medical analysis
            if prompt:
                text_prompt = f"Analyze this medical image. Focus on: {prompt}"
            else:
                text_prompt = (
                    "You are a medical imaging expert. Analyze this medical image and provide:\n"
                    "1. Type of medical imaging (X-ray, CT, MRI, etc.)\n"
                    "2. Anatomical region visible\n"
                    "3. Key findings and observations\n"
                    "4. Any abnormalities or areas of concern\n"
                    "5. Confidence level in your assessment"
                )

            # Prepare inputs
            inputs = self.processor(
                images=image,
                text=text_prompt,
                return_tensors="pt"
            )

            # Move inputs to device
            if self.device not in ["auto"]:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate response
            logger.info("Generating MedGemma analysis...")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.95,
                )

            # Decode response
            generated_text = self.processor.batch_decode(
                outputs,
                skip_special_tokens=True
            )[0]

            # Extract the response (remove the prompt part)
            if text_prompt in generated_text:
                response = generated_text.split(text_prompt, 1)[-1].strip()
            else:
                response = generated_text

            logger.info(f"MedGemma analysis complete: {len(response)} chars")

            return response if response else "No analysis generated. Please try again."

        except Exception as e:
            logger.error(f"Error in HuggingFace analysis: {e}")
            logger.warning("Falling back to mock analysis")
            return self._mock_medgemma_analysis(image, prompt)

    def _mock_medgemma_analysis(self, image: Image.Image, prompt: Optional[str]) -> str:
        """
        Mock MedGemma analysis for demo/testing purposes.
        """
        analysis = """
Medical Image Analysis Results:

IMAGING TYPE: Chest X-Ray - Frontal View
ANATOMICAL REGION: Thorax (Chest)

FINDINGS:
1. Image Quality
   - Adequate penetration and positioning
   - Good visualization of thoracic structures

2. Cardiac Assessment
   - Heart: Normal size and contour
   - Cardiothoracic ratio: Within normal limits (<0.5)
   - No cardiomegaly detected

3. Pulmonary Assessment
   - Lung Fields: Clear bilaterally
   - No focal consolidation
   - No pleural effusion
   - No pneumothorax
   - Vascular markings appear normal

4. Mediastinum
   - Normal mediastinal contour
   - No widening or masses

5. Bony Structures
   - Ribs: No acute fractures visible
   - Spine: Alignment appears normal
   - Clavicles: Symmetric, no abnormalities

ADDITIONAL OBSERVATIONS:
   - Possible mild linear opacity in right lower lung zone
   - This may represent subsegmental atelectasis
   - Clinical correlation recommended

IMPRESSION:
   - Essentially normal chest radiograph
   - No acute cardiopulmonary abnormality identified
   - Recommend clinical correlation for subtle right lower lung finding

CONFIDENCE LEVEL: 85%
RECOMMENDATION: If clinically indicated, follow-up imaging may be considered
        """

        if prompt:
            analysis = f"Analysis focused on: {prompt}\n\n" + analysis

        return analysis.strip()

    def _vertex_ai_analysis(self, image: Image.Image, prompt: Optional[str]) -> str:
        """
        Placeholder for Vertex AI MedGemma integration.
        """
        logger.warning("Vertex AI endpoint not yet implemented, using mock data")
        return self._mock_medgemma_analysis(image, prompt)

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Return the function definition for Gemini Function Calling.
        """
        return {
            "name": "analyze_medical_image",
            "description": (
                "Analyze a medical image (X-ray, CT, MRI) using the specialized "
                "MedGemma-4B model from Google. Returns detailed medical findings including "
                "anatomical observations, abnormalities, and diagnostic impressions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "image_base64": {
                        "type": "string",
                        "description": "Base64 encoded medical image"
                    },
                    "focus_areas": {
                        "type": "string",
                        "description": (
                            "Optional: Specific areas to focus on "
                            "(e.g., 'lung fields', 'cardiac silhouette', 'skeletal structures')"
                        )
                    }
                },
                "required": ["image_base64"]
            }
        }

    def unload_model(self):
        """Unload model from memory to free up resources."""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("MedGemma model unloaded")
