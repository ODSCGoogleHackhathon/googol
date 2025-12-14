"""API client for communicating with the MedAnnotator backend."""

import requests
from typing import List, Optional, Dict, Any
import streamlit as st

# Backend URL - configurable
API_URL = "http://localhost:8000"


def health_check() -> tuple[bool, Dict[str, Any]]:
    """Check backend health."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}


def load_dataset(data_name: str, image_paths: List[str]) -> Dict[str, Any]:
    """Load dataset into backend."""
    try:
        response = requests.post(
            f"{API_URL}/datasets/load",
            json={"data_name": data_name, "data": image_paths},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return {"success": False, "error": str(e)}


def analyze_dataset(data_name: str, prompt: str, flagged: Optional[List[str]] = None) -> Dict[str, Any]:
    """Analyze dataset with MedGemma."""
    try:
        response = requests.post(
            f"{API_URL}/datasets/analyze",
            json={"data_name": data_name, "prompt": prompt, "flagged": flagged},
            timeout=600  # 10 minutes for batch processing
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error analyzing dataset: {e}")
        return {"success": False, "error": str(e)}


def get_annotations(data_name: str) -> Dict[str, Any]:
    """Get all annotations for dataset."""
    try:
        response = requests.get(f"{API_URL}/datasets/{data_name}/annotations", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting annotations: {e}")
        return {"dataset_name": data_name, "total_annotations": 0, "annotations": []}


def update_annotation(data_name: str, img_path: str, new_label: str, new_desc: str) -> Dict[str, Any]:
    """Update annotation (relabel)."""
    try:
        response = requests.patch(
            f"{API_URL}/annotations",
            json={"data_name": data_name, "img": img_path, "new_label": new_label, "new_desc": new_desc},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error updating annotation: {e}")
        return {"success": False, "error": str(e)}


def delete_annotation(data_name: str, img_path: str) -> Dict[str, Any]:
    """Delete annotation (remove)."""
    try:
        response = requests.delete(
            f"{API_URL}/annotations",
            json={"data_name": data_name, "img": img_path},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error deleting annotation: {e}")
        return {"success": False, "error": str(e)}


def chat_with_ai(message: str, dataset_name: Optional[str] = None, chat_history: Optional[List[dict]] = None) -> Dict[str, Any]:
    """Send message to AI chatbot."""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"message": message, "dataset_name": dataset_name, "chat_history": chat_history},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error in chat: {e}")
        return {"success": False, "ai_message": "", "error": str(e)}


def export_dataset(data_name: str) -> Dict[str, Any]:
    """Export dataset annotations."""
    try:
        response = requests.get(f"{API_URL}/datasets/{data_name}/export", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error exporting dataset: {e}")
        return {"dataset_name": data_name, "total_annotations": 0, "annotations": []}
