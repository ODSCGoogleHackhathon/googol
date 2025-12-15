"""MedGemma integration tool for medical image analysis using HuggingFace."""

import logging
from typing import Optional, Dict, Any
import base64
from io import BytesIO
from PIL import Image
import torch
import requests

from transformers import AutoProcessor, AutoModelForImageTextToText

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
        self._model_loaded = False

        logger.info(f"Initializing MedGemma tool with endpoint: {self.endpoint}")

        # Lazy loading: Don't load model at startup to allow fast container startup
        # Model will be loaded on first use
        if self.endpoint == "huggingface":
            logger.info("MedGemma will be loaded on first use (lazy loading)")

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
                token=settings.huggingface_token if settings.huggingface_token else None,
            )

            # Load model - using AutoModelForImageTextToText for MedGemma
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                cache_dir=self.cache_dir,
                torch_dtype=torch.bfloat16 if self.device in ["cuda", "mps"] else torch.float32,
                device_map="auto" if self.device == "auto" else None,
                token=settings.huggingface_token if settings.huggingface_token else None,
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
            # If no API is available, use the loaded HuggingFace model
            if settings.medgemma_api_domain is None:
                # Lazy load model on first use
                if self.endpoint == "huggingface" and not self._model_loaded:
                    logger.info("First MedGemma request - loading model now...")
                    self._load_huggingface_model()
                    self._model_loaded = True

                # Decode image
                image_data = base64.b64decode(image_base64)
                image = Image.open(BytesIO(image_data))

                image = image.convert("RGB")

                logger.info(f"Analyzing image of size: {image.size}, mode: {image.mode}")

                # Route to appropriate endpoint
                return self._huggingface_analysis(image, prompt)
            # Run with API instead
            else:
                logger.info('RUNNING API REQUEST')
                res = requests.post(
                    f'http://{settings.medgemma_api_domain}/annotate/',
                    json={
                        "prompt": prompt if prompt else "Analyse the image",
                        "img_b64": image_base64
                    }, timeout=600
                )
                logger.info(f'MEDGEMMA RESPONSE: {res.json()}')
                return res.json()['medgemma_response']

        except Exception as e:
            logger.error(f"Error analyzing image with MedGemma: {e}")
            return f"Error during analysis: {str(e)}"

    def _huggingface_analysis(self, image: Image.Image, prompt: Optional[str]) -> str:
        """
        Analyze medical image using HuggingFace MedGemma model.
        Uses chat template format as per MedGemma documentation.
        """
        try:
            # Create prompt for medical analysis
            if prompt:
                user_text = f"Analyze this medical image. Focus on: {prompt}"
            else:
                user_text = (
                    "Analyze this medical image and provide:\n"
                    "1. Type of medical imaging (X-ray, CT, MRI, etc.)\n"
                    "2. Anatomical region visible\n"
                    "3. Key findings and observations\n"
                    "4. Any abnormalities or areas of concern\n"
                    "5. Confidence level in your assessment"
                )

            # Format as chat messages (MedGemma's required format)
            messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are an expert radiologist."}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image", "image": image},
                    ],
                },
            ]

            # Apply chat template
            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            )

            # Move to device
            if self.device not in ["auto"]:
                inputs = inputs.to(self.device, dtype=torch.bfloat16)
            else:
                inputs = inputs.to(self.model.device, dtype=torch.bfloat16)

            input_len = inputs["input_ids"].shape[-1]

            # Generate response
            logger.info("Generating MedGemma analysis...")
            with torch.inference_mode():
                generation = self.model.generate(
                    **inputs,
                    max_new_tokens=2048,  # Increased for detailed medical analysis
                    do_sample=False,
                )
                generation = generation[0][input_len:]

            # Decode response
            response = self.processor.decode(generation, skip_special_tokens=True)

            logger.info(f"MedGemma analysis complete: {len(response)} chars")

            return response if response else "No analysis generated. Please try again."

        except Exception as e:
            logger.error(f"Error in HuggingFace analysis: {e}")
            raise  # Re-raise to see the full error

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
                        "description": "Base64 encoded medical image",
                    },
                    "focus_areas": {
                        "type": "string",
                        "description": (
                            "Optional: Specific areas to focus on "
                            "(e.g., 'lung fields', 'cardiac silhouette', 'skeletal structures')"
                        ),
                    },
                },
                "required": ["image_base64"],
            },
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
