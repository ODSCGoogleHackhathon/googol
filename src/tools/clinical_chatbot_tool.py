"""Clinical Assistant chatbot tool for grounded Q&A using annotation data from the two-tier architecture."""

import logging
from typing import Optional, Dict, Any
import google.generativeai as genai

from DB.agentic_repository import AgenticAnnotationRepo

logger = logging.getLogger(__name__)


class ClinicalChatbotTool:
    """
    Clinical Assistant chatbot that provides grounded Q&A by accessing:
    - Finalized structured annotation data (clean summaries)
    - Raw pipeline outputs from annotation_request table
    - MedGemma analysis results
    """

    def __init__(self, model: genai.GenerativeModel, repo: AgenticAnnotationRepo):
        """
        Initialize the Clinical Assistant chatbot.

        Args:
            model: Gemini GenerativeModel instance (shared with agent)
            repo: AgenticAnnotationRepo instance for database access
        """
        self.model = model
        self.repo = repo
        logger.info("ClinicalChatbotTool initialized")

    def _get_annotation_with_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Helper method to get annotation with request data using request_id.
        
        Since get_annotation_with_request uses set_name and path_url, this method:
        1. Gets the annotation_request by request_id
        2. Uses set_name and path_url from that to get the annotation
        3. Combines both into a single dict
        
        Args:
            request_id: The annotation_request ID
            
        Returns:
            Combined dict with annotation and request data, or None if not found
        """
        # First, get the annotation_request
        request_data = self.repo.get_annotation_request(request_id)
        if not request_data:
            logger.warning(f"Annotation request {request_id} not found")
            return None
        
        # Extract set_name and path_url
        set_name = request_data.get('set_name')
        path_url = request_data.get('path_url')
        
        if not set_name or not path_url:
            logger.warning(f"Invalid request data for request_id {request_id}")
            return None
        
        # Get the annotation with request data
        annotation_data = self.repo.get_annotation_with_request(set_name, path_url)
        
        if not annotation_data:
            # If annotation doesn't exist yet, return just the request data
            logger.info(f"Annotation not found for request_id {request_id}, returning request data only")
            return request_data
        
        # Merge request data into annotation_data (request data takes precedence for overlapping fields)
        combined = {**annotation_data, **request_data}
        return combined

    def answer_question(self, request_id: int, question: str) -> str:
        """
        Answer a clinical question based on grounded annotation data.

        This method is designed to be called by GeminiAnnotationAgent when it determines
        the user has a query (a "Reasoning" step in ReAct).

        Args:
            request_id: The annotation_request ID to fetch data for
            question: The user's question

        Returns:
            Clinical assistant's response based on the grounded data
        """
        try:
            # Fetch combined data from both annotation and annotation_request tables
            data = self._get_annotation_with_request_by_id(request_id)
            
            if not data:
                return f"I couldn't find annotation data for request ID {request_id}. Please verify the request ID exists."

            # Extract key fields for the prompt
            clean_summary = data.get('desc', 'N/A')  # Clean summary from annotation table
            medgemma_raw = data.get('medgemma_raw', 'N/A')  # Raw MedGemma output
            confidence_score = data.get('confidence_score', 0.0)  # Confidence score
            
            # Additional context that might be useful
            gemini_validated = data.get('gemini_validated', {})
            pydantic_output = data.get('pydantic_output', {})
            findings = pydantic_output.get('findings', []) if isinstance(pydantic_output, dict) else []
            gemini_report = data.get('gemini_report')
            validation_status = data.get('validation_status', 'unknown')
            path_url = data.get('path_url', 'N/A')
            
            # Construct highly-specific prompt for Gemini
            prompt = f"""You are a Clinical Assistant helping medical professionals understand and interpret medical image annotation results.

**IMPORTANT:** Answer the user's question based ONLY on the following provided context. Do not make assumptions beyond what is provided.

**User's Question:** {question}

**Context Data:**

1. **Clean Summary (Highest Priority - Use this for polished answers):**
{clean_summary}

2. **Raw MedGemma Output (For traceability/debugging questions):**
{medgemma_raw}

3. **Confidence Score:**
{confidence_score:.2f} (on a scale of 0.0 to 1.0)

4. **Additional Context:**
- Image Path: {path_url}
- Validation Status: {validation_status}
- Number of Findings: {len(findings)}
"""

            # Add findings if available
            if findings:
                prompt += "\n**Structured Findings:**\n"
                for i, finding in enumerate(findings, 1):
                    if isinstance(finding, dict):
                        label = finding.get('label', 'Unknown')
                        location = finding.get('location', 'N/A')
                        severity = finding.get('severity', 'N/A')
                        prompt += f"{i}. {label} - Location: {location}, Severity: {severity}\n"
            
            # Add Gemini report if available
            if gemini_report:
                prompt += f"\n**Professional Report:**\n{gemini_report}\n"
            
            prompt += """
**Instructions:**
- Provide a clear, professional, and medically accurate answer to the user's question
- Reference specific findings, locations, or confidence scores when relevant
- If the question cannot be answered from the provided context, clearly state that
- Use the clean summary as the primary source, but refer to raw data if asked about traceability
- Maintain a clinical, professional tone appropriate for medical professionals
"""

            # Generate response using the model (which already has safety settings configured)
            logger.info(f"Generating clinical assistant response for request_id {request_id}")
            response = self.model.generate_content(prompt)
            
            return response.text if response.text else "I apologize, but I couldn't generate a response. Please try again."

        except Exception as e:
            logger.error(f"Error in clinical chatbot answer_question: {e}", exc_info=True)
            return f"I encountered an error while processing your question: {str(e)}. Please try again or contact support."

