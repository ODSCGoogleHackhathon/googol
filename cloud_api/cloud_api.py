from fastapi import FastAPI

from transformers import pipeline
from PIL import Image
import requests
import torch
import logging
from pydantic import BaseModel
import os

app = FastAPI()

logger = logging.getLogger(__name__)

pipe = pipeline(
    "image-text-to-text",
    model="google/medgemma-4b-it",
    torch_dtype=torch.bfloat16,
    device="cpu",
    token=os.environ['HF_TOKEN']
)

@app.get("/health/")
async def root():
    return {"success": True}

class AnnotationPayload(BaseModel):
    prompt: str
    img_b64: str

@app.post("/annotate/")
async def annotate_image(request: AnnotationPayload):
    try:
    
        prompt = request.prompt
        img = request.img_b64

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are an expert radiologist."}]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "image": img}
                ]
            }
        ]
        logger.info('Running inference')
        output = pipe(text=messages, max_new_tokens=200)

        return {
            "success": True,
            "medgemma_response":  output[0]["generated_text"][-1]["content"]
        }

    except Exception as e:
        logger.error('Error: ', e)
        return {
            "success": False,
            "msg": e
        }