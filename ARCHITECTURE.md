# MedAnnotator Architecture

## High-Level System Overview

MedAnnotator is an LLM-Assisted Multimodal Medical Image Annotation Tool that uses Google Gemini and MedGemma to provide structured medical image analysis.

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                      (Streamlit Web App)                        │
│  - Image Upload                                                 │
│  - Patient ID & Instructions Input                             │
│  - Annotation Results Display                                  │
│  - JSON Editor & Download                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API LAYER                          │
│                         (FastAPI)                               │
│  - /annotate: Main annotation endpoint                         │
│  - /health: System health check                                │
│  - CORS & Request validation                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT ORCHESTRATOR                         │
│                   (GeminiAnnotationAgent)                       │
│                                                                 │
│  ReAct Pattern Implementation:                                 │
│  1. Reason: Analyze the request                                │
│  2. Act: Call MedGemma tool                                    │
│  3. Observe: Process MedGemma output                           │
│  4. Structure: Generate JSON with Gemini                       │
└─────────────┬────────────────────────────────┬──────────────────┘
              │                                │
              ▼                                ▼
    ┌──────────────────┐           ┌──────────────────────┐
    │   MEDGEMMA TOOL  │           │    GEMINI API        │
    │                  │           │  (gemini-2.0-flash)  │
    │ - Image Analysis │           │                      │
    │ - Medical Insight│           │ - JSON Structuring   │
    │ - Mock/Real API  │           │ - Reasoning          │
    └──────────────────┘           │ - Function Calling   │
                                   └──────────────────────┘
```

## Component Details

### 1. User Interface (Streamlit)
**Location:** `src/ui/app.py`

**Responsibilities:**
- Provide intuitive image upload interface
- Display uploaded medical images
- Accept optional patient ID and user prompts
- Show structured annotation results
- Enable JSON editing and download
- Display system health status

**Technologies:**
- Streamlit for rapid UI development
- PIL for image handling
- Requests for backend communication

### 2. Backend API (FastAPI)
**Location:** `src/api/main.py`

**Responsibilities:**
- Expose REST endpoints for annotation
- Validate incoming requests
- Manage agent lifecycle
- Handle errors gracefully
- Provide health checks

**Endpoints:**
- `GET /`: API information
- `GET /health`: System health status
- `POST /annotate`: Image annotation endpoint

**Technologies:**
- FastAPI for async API framework
- Pydantic for request/response validation
- CORS middleware for cross-origin requests

### 3. Agent Core (Gemini Annotation Agent)
**Location:** `src/agent/gemini_agent.py`

**Architecture Pattern:** ReAct (Reasoning + Acting)

**Workflow:**
1. **Receive Request**: Image (base64) + optional prompt
2. **Plan**: Determine analysis strategy
3. **Execute Tool**: Call MedGemma for medical analysis
4. **Process Results**: Use Gemini to structure output
5. **Return**: Structured JSON annotation

**Key Features:**
- Multi-step reasoning
- Tool orchestration
- Error handling with fallbacks
- JSON schema enforcement

### 4. MedGemma Tool
**Location:** `src/tools/medgemma_tool.py`

**Purpose:** Medical image analysis using specialized model

**Implementation:**
- **MVP/Demo Mode**: Mock analysis with realistic medical findings
- **Production Mode**: Integration with actual MedGemma via Vertex AI or Hugging Face

**Output:** Textual medical analysis with findings, impressions, and confidence

### 5. Gemini Integration
**API:** Google Generative AI (google-generativeai)

**Model:** gemini-2.0-flash-exp

**Capabilities Used:**
- Multimodal understanding
- JSON mode for structured output
- Function calling (planned for future)
- ReAct-style reasoning

### 6. Data Models & Schemas
**Location:** `src/schemas.py`

**Key Models:**
- `Finding`: Individual medical observation
- `AnnotationOutput`: Complete structured annotation
- `AnnotationRequest`: API request format
- `AnnotationResponse`: API response format

**JSON Output Schema:**
```json
{
  "patient_id": "string",
  "findings": [
    {
      "label": "string",
      "location": "string",
      "severity": "string"
    }
  ],
  "confidence_score": 0.0-1.0,
  "generated_by": "string",
  "additional_notes": "string"
}
```

## Data Flow

1. **User uploads image** → Streamlit UI
2. **Image encoded to base64** → Sent to FastAPI backend
3. **FastAPI validates request** → Passes to Agent
4. **Agent calls MedGemma tool** → Gets medical analysis
5. **Agent uses Gemini** → Structures analysis into JSON
6. **Response returned** → Displayed in UI
7. **User reviews/edits** → Can download JSON

## Observability & Logging

**Logging Strategy:**
- Python logging module with configurable levels
- File logging: `logs/app.log`
- Console logging for development
- Structured log messages with timestamps

**Logged Events:**
- Agent initialization
- Annotation requests
- Tool calls
- Processing times
- Errors and exceptions

**Error Handling:**
- Try-catch blocks at each layer
- Graceful fallbacks for parsing errors
- User-friendly error messages
- Detailed error logging for debugging

## Configuration Management
**Location:** `src/config.py`

**Method:** Environment variables via `.env` file

**Key Settings:**
- API keys (Gemini, Google Cloud)
- Model selection
- Endpoint configuration
- Logging levels
- Port configuration

## Deployment Architecture

**Development:**
- Backend: `python -m src.api.main` (localhost:8000)
- Frontend: `streamlit run src/ui/app.py` (localhost:8501)

**Production Considerations:**
- Containerize with Docker
- Deploy backend to Cloud Run or App Engine
- Deploy frontend to Streamlit Cloud
- Use secrets manager for API keys
- Add authentication/authorization
- Rate limiting and quotas

## Security Considerations

1. **API Key Management**: Environment variables, never committed
2. **Input Validation**: Pydantic models validate all inputs
3. **CORS**: Configured (currently permissive for hackathon)
4. **Image Processing**: Size limits and format validation
5. **Error Messages**: No sensitive information leaked

## Scalability Considerations

1. **Async Operations**: FastAPI async endpoints
2. **Stateless Design**: No server-side session storage
3. **Caching**: Can add Redis for repeated analyses
4. **Load Balancing**: Multiple backend instances possible
5. **Database**: Can add PostgreSQL for annotation storage

## Future Enhancements

1. **RAG Integration**: Add medical guideline knowledge base
2. **True MedGemma**: Connect to real MedGemma API
3. **Bounding Boxes**: Visual overlay on images
4. **Chat Mode**: Follow-up questions about findings
5. **Batch Processing**: Multiple image analysis
6. **Annotation History**: Store and retrieve past annotations
7. **User Authentication**: Multi-user support
8. **Export Formats**: PDF, DICOM SR, HL7 FHIR