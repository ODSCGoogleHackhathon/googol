"""Medical Assistant Chatbot powered by Gemini for interacting with flagged images and MedGemma analysis."""

import logging
import json
from typing import Optional, List, Dict, Any
import google.generativeai as genai

from src.config import settings

logger = logging.getLogger(__name__)


class MedicalChatbotTool:
    """
    Gemini-powered medical assistant chatbot that can:
    - Answer questions about flagged images
    - Discuss MedGemma analysis results
    - Provide insights on dataset findings
    - Assist with medical image annotation tasks
    """

    def __init__(self):
        """Initialize the chatbot with Gemini."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.gemini_temperature,
                "max_output_tokens": settings.gemini_max_tokens,
            },
        )
        logger.info(f"MedicalChatbotTool initialized with model: {settings.gemini_model}")

    def _get_flagged_images(self, db_repo, dataset_name: str) -> List[Dict[str, Any]]:
        """
        Retrieve flagged images from the annotation table.
        
        Args:
            db_repo: AnnotationRepo instance
            dataset_name: Dataset identifier
            
        Returns:
            List of flagged annotation dicts
        """
        try:
            annotations = db_repo.get_annotations(dataset_name)
            flagged = []
            
            for ann in annotations:
                # Check if description starts with [FLAGGED]
                desc = ann[4] if len(ann) > 4 else ""  # desc is typically at index 4
                if desc and desc.startswith("[FLAGGED]"):
                    flagged.append({
                        "path": ann[1],  # path_url
                        "label": ann[2],  # label
                        "patient_id": ann[3],  # patient_id
                        "description": desc,
                        "request_id": ann[5] if len(ann) > 5 else None  # request_id
                    })
            
            return flagged
        except Exception as e:
            logger.error(f"Error retrieving flagged images: {e}")
            return []

    def _get_medgemma_analysis(self, agentic_repo, dataset_name: str, path_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve MedGemma analysis from annotation_request table.
        
        Args:
            agentic_repo: AgenticAnnotationRepo instance
            dataset_name: Dataset identifier
            path_url: Optional specific image path
            
        Returns:
            List of analysis dicts with MedGemma and Gemini data
        """
        try:
            if path_url:
                # Get specific request
                requests = agentic_repo.get_unprocessed_requests(set_name=dataset_name)
                requests = [r for r in requests if r['path_url'] == path_url]
            else:
                # Get all requests for dataset
                requests = agentic_repo.get_unprocessed_requests(set_name=dataset_name)
            
            analyses = []
            for req in requests:
                analyses.append({
                    "path_url": req['path_url'],
                    "medgemma_raw": req.get('medgemma_raw', ''),
                    "gemini_validated": req.get('gemini_validated', {}),
                    "pydantic_output": req.get('pydantic_output', {}),
                    "confidence_score": req.get('confidence_score', 0.0),
                    "validation_status": req.get('validation_status', 'unknown'),
                    "gemini_enhanced": req.get('gemini_enhanced', False),
                    "gemini_report": req.get('gemini_report'),
                    "urgency_level": req.get('urgency_level'),
                    "clinical_significance": req.get('clinical_significance'),
                })
            
            return analyses
        except Exception as e:
            logger.error(f"Error retrieving MedGemma analysis: {e}")
            return []

    def _build_context(
        self,
        dataset_name: Optional[str],
        db_repo=None,
        agentic_repo=None,
        flagged_paths: Optional[List[str]] = None
    ) -> str:
        """
        Build context string from dataset, flagged images, and MedGemma analysis.
        
        Args:
            dataset_name: Dataset identifier
            db_repo: AnnotationRepo instance
            agentic_repo: AgenticAnnotationRepo instance
            flagged_paths: Optional list of specific flagged image paths to focus on
            
        Returns:
            Context string for the chatbot
        """
        context_parts = []
        
        if not dataset_name:
            return ""
        
        # Dataset overview
        if db_repo:
            try:
                annotations = db_repo.get_annotations(dataset_name)
                if annotations:
                    labels = {}
                    flagged_count = 0
                    for ann in annotations:
                        label = ann[2] if len(ann) > 2 else "unknown"
                        labels[label] = labels.get(label, 0) + 1
                        desc = ann[4] if len(ann) > 4 else ""
                        if desc and desc.startswith("[FLAGGED]"):
                            flagged_count += 1
                    
                    context_parts.append(f"Dataset '{dataset_name}' Overview:")
                    context_parts.append(f"- Total images: {len(annotations)}")
                    context_parts.append(f"- Flagged images: {flagged_count}")
                    context_parts.append(f"- Label distribution: {dict(labels)}")
            except Exception as e:
                logger.warning(f"Error building dataset context: {e}")
        
        # Flagged images details
        if db_repo:
            flagged_images = self._get_flagged_images(db_repo, dataset_name)
            if flagged_images:
                if flagged_paths:
                    # Filter to specific paths if provided
                    flagged_images = [f for f in flagged_images if f['path'] in flagged_paths]
                
                if flagged_images:
                    context_parts.append(f"\nFlagged Images ({len(flagged_images)}):")
                    for img in flagged_images[:10]:  # Limit to 10 for context size
                        context_parts.append(
                            f"- {img['path']}: Label={img['label']}, "
                            f"Description={img['description'][:100]}..."
                        )
        
        # MedGemma analysis details
        if agentic_repo:
            analyses = self._get_medgemma_analysis(agentic_repo, dataset_name)
            if analyses:
                if flagged_paths:
                    # Filter to specific paths if provided
                    analyses = [a for a in analyses if a['path_url'] in flagged_paths]
                
                if analyses:
                    context_parts.append(f"\nMedGemma Analysis Results ({len(analyses)}):")
                    for analysis in analyses[:5]:  # Limit to 5 for context size
                        findings = analysis.get('pydantic_output', {}).get('findings', [])
                        context_parts.append(
                            f"- {analysis['path_url']}: "
                            f"Confidence={analysis.get('confidence_score', 0):.2f}, "
                            f"Findings={len(findings)}, "
                            f"Status={analysis.get('validation_status', 'unknown')}"
                        )
                        if findings:
                            finding_labels = [f.get('label', 'unknown') for f in findings[:3]]
                            context_parts.append(f"  Findings: {', '.join(finding_labels)}")
                        if analysis.get('gemini_report'):
                            context_parts.append(f"  Report: {analysis['gemini_report'][:150]}...")
        
        return "\n".join(context_parts) if context_parts else ""

    def chat(
        self,
        message: str,
        dataset_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        db_repo=None,
        agentic_repo=None,
        flagged_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a response using Gemini with context about the dataset.
        
        Args:
            message: User's message
            dataset_name: Optional dataset identifier for context
            chat_history: Previous conversation messages
            db_repo: AnnotationRepo instance for database access
            agentic_repo: AgenticAnnotationRepo instance for MedGemma analysis
            flagged_paths: Optional list of specific flagged image paths to focus on
            
        Returns:
            AI response string
        """
        try:
            # Build system prompt with context
            system_prompt = """You are a specialized medical AI assistant helping radiologists and medical professionals with image annotation and analysis.

Your capabilities:
- Answer questions about flagged medical images
- Explain MedGemma analysis results and findings
- Provide insights on dataset statistics and patterns
- Assist with medical terminology and diagnostic guidance
- Help interpret confidence scores and validation status
- Discuss clinical significance and urgency levels

Always:
- Be professional and medically accurate
- Reference specific images by their paths when relevant
- Explain technical findings in accessible language
- Suggest next steps when appropriate
- Acknowledge limitations and recommend human review for critical cases

"""
            
            # Add dataset context
            context = self._build_context(
                dataset_name=dataset_name,
                db_repo=db_repo,
                agentic_repo=agentic_repo,
                flagged_paths=flagged_paths
            )
            
            if context:
                system_prompt += f"\nCurrent Dataset Context:\n{context}\n"
            
            # Build conversation history
            conversation = []
            
            # Add system message
            conversation.append({
                "role": "user",
                "parts": [system_prompt]
            })
            
            # Add conversation history if provided
            if chat_history:
                for msg in chat_history[-10:]:  # Last 10 messages for context
                    # Handle different formats: {"name": "ai"/"user", "content": "..."} or {"role": "...", "content": "..."}
                    name = msg.get("name", "")
                    role = msg.get("role", "")
                    
                    # Map "ai" to "model" for Gemini, "user" stays "user"
                    if name == "ai":
                        role = "model"
                    elif name == "user":
                        role = "user"
                    elif role not in ["user", "model"]:
                        role = "user"
                    
                    content = msg.get("content", "") or msg.get("message", "")
                    if content:
                        conversation.append({
                            "role": role,
                            "parts": [content]
                        })
            
            # Add current user message
            conversation.append({
                "role": "user",
                "parts": [message]
            })
            
            # Generate response
            logger.info(f"Generating chatbot response for dataset: {dataset_name}")
            response = self.model.generate_content(conversation)
            
            return response.text if response.text else "I apologize, but I couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"Error in chatbot: {e}", exc_info=True)
            return f"I encountered an error: {str(e)}. Please try again or contact support."

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Return the function definition for integration with other systems.
        """
        return {
            "name": "medical_chatbot",
            "description": (
                "Medical AI assistant chatbot powered by Gemini. Can answer questions about "
                "flagged images, MedGemma analysis results, dataset statistics, and provide "
                "medical annotation assistance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "User's message or question"
                    },
                    "dataset_name": {
                        "type": "string",
                        "description": "Optional dataset identifier for context"
                    },
                    "flagged_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific flagged image paths to focus on"
                    }
                },
                "required": ["message"]
            }
        }

