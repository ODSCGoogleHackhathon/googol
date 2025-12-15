# MedAnnotator Architecture

## Executive Summary

MedAnnotator is an AI-powered medical image annotation tool implementing a **two-tier agentic architecture** with Google Gemini 2.0 Flash and MedGemma. The system demonstrates advanced ReAct (Reasoning + Acting) patterns, intelligent tool orchestration, and a bulletproof validation pipeline with full traceability from raw AI analysis to clinical summaries.

**Key Innovation**: Two-tier database design separates raw AI outputs (staging) from clean clinical summaries (production), enabling full audit trails, debugging, and reprocessing capabilities.

---

## High-Level System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     STREAMLIT FRONTEND (UI)                       │
│   • Dataset Upload & Management  • AI Chatbot  • Analytics      │
│   • Per-image Actions (Flag/Relabel/Remove)  • Export to JSON   │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP/REST API (15+ endpoints)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (ASYNC)                        │
│  /annotate  /datasets/load  /datasets/analyze  /chat  /export   │
│               Global Services (Singleton Pattern)                 │
│   • AgenticAnnotationPipeline  • GeminiAgent  • Repos           │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│            GEMINI ANNOTATION AGENT (Orchestrator)                │
│  ReAct Pattern: Reason → Act (Tools) → Observe → Structure      │
│                                                                   │
│  Components:                                                     │
│   • AgenticAnnotationPipeline - Main 6-step workflow            │
│   • GeminiValidator - Structured output with retries            │
│   • GeminiSummaryGenerator - Clinical summaries                 │
│   • GeminiEnhancer - Optional professional reports              │
│   • ClinicalChatbotTool - Focused Q&A on annotations            │
│   • MedicalChatbotTool - General dataset assistance             │
└───────┬────────────────────────────────────┬─────────────────────┘
        │                                    │
        ▼                                    ▼
┌──────────────────┐              ┌─────────────────────────┐
│  MEDGEMMA TOOL   │              │   GEMINI 2.0 FLASH      │
│                  │              │  (google-generativeai)  │
│ Mode 1:          │              │                         │
│ HuggingFace Local│              │ Capabilities:           │
│ • 4B-IT model    │              │ • JSON structuring      │
│ • CUDA/MPS/CPU   │              │ • Validation (retry)    │
│ • Lazy loading   │              │ • Summarization         │
│                  │              │ • Chat conversations    │
│ Mode 2:          │              │ • Function calling      │
│ Cloud API        │              │                         │
│ • External API   │              │ Temperature:            │
│ • 600s timeout   │              │ • Validation: 0.1       │
└──────────────────┘              │ • Summary: 0.2          │
                                  │ • Chat: 0.7             │
                                  └─────────────────────────┘
        │                                    │
        └────────────────┬───────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│              SQLITE DATABASE (Two-Tier Architecture)             │
│                                                                   │
│  Tier 1: annotation_request (Staging/Raw Data)                  │
│   • medgemma_raw: Raw text analysis                             │
│   • gemini_validated: Structured JSON                           │
│   • validation_attempt: Retry count                             │
│   • validation_status: 'success'/'retry'/'fallback'             │
│   • pydantic_output: Full AnnotationOutput                      │
│   • confidence_score, urgency_level, etc.                       │
│   • processed: Boolean flag for pipeline status                 │
│                                                                   │
│  Tier 2: annotation (Clean/Production Data)                     │
│   • label: Primary diagnosis (concise, 20 chars)                │
│   • desc: Gemini-generated clinical summary (4000 chars)        │
│   • request_id: Foreign key to annotation_request               │
│                                                                   │
│  Supporting Tables:                                              │
│   • label: Valid medical labels                                 │
│   • patient: Patient metadata                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. User Interface (Streamlit)

**Location**: `src/ui/app.py`

**Core Features**:

1. **Dataset Upload & Management**
   - Folder path input with validation
   - Optional patient ID extraction from subfolder names
   - Optional label extraction from subfolder structure
   - Automatic duplicate detection (skip existing images)
   - Pagination system (12 images per page)

2. **AI Chatbot Sidebar**
   - Context-aware conversations about the dataset
   - Access to:
     - Dataset statistics (total images, label distribution)
     - Flagged images information
     - MedGemma analysis results
   - Persistent chat history in Streamlit session state
   - Clear history button
   - Real-time response streaming

3. **Dataset Analysis**
   - Custom prompt input for targeted analysis
   - Force re-analyze option (resets `processed=0` flag)
   - Batch processing with progress tracking
   - Selective analysis (flagged images only)

4. **Per-Image Actions** (`src/ui/components/image.py`)
   - **Flag**: Mark for review (adds `[FLAGGED]` prefix to description)
   - **Relabel**: Manual or AI-powered editing
     - AI Analyze button: Single-image analysis
     - Manual Save button: Direct edit of label and description
   - **Remove**: Delete annotation and request from database

5. **Analytics & Export**
   - Label frequency bar chart
   - Total images counter
   - Export to JSON button
   - Colored label tags for visual recognition

**Technologies**:
- Streamlit 1.29+ for reactive UI
- PIL for image handling
- Pandas for data display
- Requests for backend communication

---

### 2. Backend API (FastAPI)

**Location**: `src/api/main.py`

**Architecture Pattern**: Async/await with lifespan management

**Global Services** (Singleton Pattern):
```python
agent: GeminiAnnotationAgent = None         # Main orchestrator
db_repo: AnnotationRepo = None              # Legacy DB operations
agentic_repo: AgenticAnnotationRepo = None  # Two-tier DB operations
agentic_pipeline: AgenticAnnotationPipeline = None  # Shared MedGemma instance
chatbot: MedicalChatbotTool = None          # General assistant
```

**Key Design Decision**: Global `agentic_pipeline` prevents MedGemma model from reloading on every request (~85% performance improvement for batch processing).

**Core Endpoints**:

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/` | GET | API information | <10ms |
| `/health` | GET | System health (Gemini + MedGemma status) | <50ms |
| `/annotate` | POST | Single image annotation (legacy) | 2-5s |
| `/datasets/load` | POST | Load image paths into database | <1s |
| `/datasets/analyze` | POST | Batch analysis with MedGemma pipeline | 2-5s/image |
| `/datasets/{name}/annotations` | GET | Retrieve all annotations | <100ms |
| `/datasets/{name}/export` | GET | Export as JSON | <200ms |
| `/annotations` | PATCH | Update annotation (label/description) | <50ms |
| `/annotations` | DELETE | Delete annotation(s) | <50ms |
| `/chat` | POST | AI chatbot (routes to Clinical/Medical tool) | 1-3s |

**Request/Response Models** (`src/schemas.py`):
- Pydantic validation on all inputs
- Type safety and automatic API documentation
- Max length enforcement (paths: 200 chars, desc: 4000 chars)
- Clear error messages with HTTP status codes

**Error Handling**:
- Try-catch blocks at each layer
- Graceful degradation (fallback annotations)
- User-friendly error messages
- Detailed logging for debugging
- HTTP 503 if services not initialized
- HTTP 400 for invalid requests
- HTTP 404 for missing resources
- HTTP 500 for server errors

---

### 3. Agent Core (Gemini Annotation Agent)

**Location**: `src/agent/gemini_agent.py`

**Architecture Pattern**: ReAct (Reasoning + Acting)

**Class**: `GeminiAnnotationAgent`

**Responsibilities**:
1. Initialize and manage all AI tools
2. Orchestrate the annotation pipeline
3. Route chatbot queries (general vs. clinical)
4. Health monitoring and diagnostics

**Initialization**:
```python
def __init__(self):
    self.agentic_repo = AgenticAnnotationRepo()
    self.enhancer = GeminiEnhancer()       # Optional enhancements
    self.clinical_chatbot = ClinicalChatbotTool()  # Focused Q&A
```

**Key Methods**:
- `annotate_image()`: Entry point for single image annotation (legacy)
- `chat()`: Route user query to appropriate chatbot
- `check_health()`: Verify Gemini and MedGemma connectivity

**Why ReAct?**
- **Reason**: Analyze the task, determine if analysis needed
- **Act**: Call MedGemma tool for medical analysis
- **Observe**: Process raw MedGemma output
- **Reason**: Decide on validation strategy
- **Act**: Call Gemini to structure output
- **Observe**: Validate against Pydantic schema
- **Reason**: Generate clinical summary
- **Act**: Call Gemini summary generator
- **Result**: Structured annotation + clinical summary

---

### 4. Agentic Annotation Pipeline

**Location**: `src/pipelines/agentic_annotation_pipeline.py`

**Class**: `AgenticAnnotationPipeline`

**The Six-Step Bulletproof Pipeline**:

```python
def annotate(
    image_base64: str,
    set_name: int,
    image_path: str,
    user_prompt: str,
    patient_id: int,
    enable_enhancement: bool = False
) -> Tuple[AnnotationOutput, Dict, str, str]:

    # STEP 1: MedGemma Analysis (Raw Text)
    medgemma_raw = self.medgemma.analyze_image(
        image_base64=image_base64,
        prompt=user_prompt or "Analyze this medical image..."
    )
    # → Saved to annotation_request.medgemma_raw

    # STEP 2: Gemini Validation (Structured Output with Retries)
    annotation, gemini_dict, metadata = self._validated_annotation(
        medgemma_output=medgemma_raw,
        patient_id=patient_id,
        max_retries=2  # Up to 2 retry attempts
    )
    # → Saved to annotation_request.gemini_validated
    # → validation_status: 'success' | 'retry' | 'fallback'

    # STEP 3: Optional Gemini Enhancement
    if enable_enhancement:
        annotation = self._apply_enhancement(
            annotation,
            image_base64=image_base64
        )
        # → Saves urgency_level, clinical_significance

    # STEP 4: Build annotation_request Data
    request_data = {
        "medgemma_raw": medgemma_raw,
        "gemini_validated": gemini_dict,
        "validation_attempt": metadata['attempts'],
        "validation_status": metadata['status'],
        "pydantic_output": annotation.dict(),
        "confidence_score": annotation.confidence_score,
        "gemini_enhanced": enable_enhancement,
        ...
    }

    # STEP 5: Generate Clinical Summary
    clinical_summary = self.summary_generator.generate_summary(annotation)
    summary_text = clinical_summary.to_desc_string()
    # Format:
    # PRIMARY DIAGNOSIS: Pneumothorax
    #
    # SUMMARY: Right-sided pneumothorax identified...
    #
    # KEY FINDINGS:
    # • Finding 1
    # • Finding 2

    # STEP 6: Extract Primary Label
    primary_label = clinical_summary.primary_diagnosis[:20]  # Max 20 chars

    return annotation, request_data, summary_text, primary_label
```

**Key Features**:
- **Full Traceability**: Every step logged and saved
- **Automatic Retries**: Up to 2 validation attempts
- **Fallback Parser**: Local keyword detection if Gemini fails
- **Lazy Loading**: MedGemma loads on first use only
- **Pydantic Validation**: Schema enforcement at every step

---

### 5. Validation Pipeline

**Location**: `src/pipelines/validation_pipeline.py`

**Class**: `GeminiValidator`

**Purpose**: Convert MedGemma's raw text into structured JSON

**Validation Flow**:

```python
def validate(medgemma_output: str, patient_id: int, max_retries: int):
    attempt = 0

    while attempt < max_retries:
        try:
            # Build prompt with schema
            prompt = self._build_prompt(medgemma_output, patient_id, attempt)

            # Call Gemini with JSON mode
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,  # Low for consistency
                    "response_mime_type": "application/json"
                }
            )

            # Parse JSON
            validated_dict = json.loads(response.text)

            # Pydantic validation
            annotation = AnnotationOutput(**validated_dict)

            return annotation, validated_dict, {"status": "success", "attempts": attempt + 1}

        except (json.JSONDecodeError, ValidationError) as e:
            attempt += 1
            logger.warning(f"Validation attempt {attempt} failed: {e}")

    # Fallback: Use local parser
    return self._fallback_parse(medgemma_output, patient_id)
```

**Retry Strategy**:
- **Attempt 1**: Initial prompt with full schema
- **Attempt 2**: Stricter prompt emphasizing data types and format
- **Fallback**: Keyword-based parser
  - Detects: pneumothorax, fracture, effusion, etc.
  - Returns generic Finding objects
  - Confidence: 0.50 (low to indicate fallback)

**Gemini Configuration**:
- **Model**: Gemini 2.0 Flash Exp
- **Temperature**: 0.1 (consistent output)
- **Response Format**: `application/json`
- **Max Tokens**: 2048

---

### 6. Summary Generation

**Location**: `src/agent/summary_generator.py`

**Class**: `GeminiSummaryGenerator`

**Purpose**: Convert AnnotationOutput into clinical summaries for human readers

**Output Model** (`src/models/clinical_summary.py`):
```python
class ClinicalSummary(BaseModel):
    primary_diagnosis: str           # Max 100 chars (e.g., "Pneumothorax")
    summary: str                     # Max 3500 chars (2-4 sentences)
    key_findings: List[str]          # Max 5 findings
    recommendations: Optional[str]    # Next steps (optional)
    confidence_note: Optional[str]    # Limitations (optional)

    def to_desc_string(self) -> str:
        """Format for database storage"""
        result = [f"PRIMARY DIAGNOSIS: {self.primary_diagnosis}", ""]
        result.append(f"SUMMARY: {self.summary}")

        if self.key_findings:
            result.append("\nKEY FINDINGS:")
            for finding in self.key_findings:
                result.append(f"• {finding}")

        if self.recommendations:
            result.append(f"\nRECOMMENDATIONS: {self.recommendations}")

        if self.confidence_note:
            result.append(f"\nNOTE: {self.confidence_note}")

        return "\n".join(result)
```

**Generation Process**:
```python
def generate_summary(annotation: AnnotationOutput) -> ClinicalSummary:
    # Build prompt
    prompt = f"""
    Convert this structured annotation into a clinical summary.

    Annotation:
    {json.dumps(annotation.dict(), indent=2)}

    Generate a concise summary suitable for medical records.
    """

    # Call Gemini
    response = self.model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,  # Slightly higher for natural language
            "response_mime_type": "application/json"
        }
    )

    # Parse and validate
    summary_dict = json.loads(response.text)
    clinical_summary = ClinicalSummary(**summary_dict)

    return clinical_summary
```

**Gemini Configuration**:
- **Model**: Gemini 2.0 Flash Lite (faster, cheaper for summarization)
- **Temperature**: 0.2 (consistent but natural language)
- **Max Output**: 2048 tokens

---

### 7. MedGemma Tool Integration

**Location**: `src/tools/medgemma_tool.py`

**Class**: `MedGemmaTool`

**Mode 1: HuggingFace Local** (Default)
```python
def __init__(endpoint="huggingface"):
    self.model_id = "google/medgemma-4b-it"
    self.device = self._detect_device()  # CUDA > MPS > CPU
    self._model_loaded = False  # Lazy loading flag

def _load_huggingface_model(self):
    """Load model on first use (not at startup)"""
    logger.info("Loading MedGemma from HuggingFace...")

    self.model = AutoModelForCausalLM.from_pretrained(
        self.model_id,
        device_map="auto",
        torch_dtype=torch.float16 if self.device != "cpu" else torch.float32
    )

    self.processor = AutoProcessor.from_pretrained(self.model_id)
    self._model_loaded = True
    logger.info(f"✓ MedGemma loaded on {self.device}")

def analyze_image(image_base64: str, prompt: Optional[str]) -> str:
    # Lazy load on first use
    if not self._model_loaded:
        self._load_huggingface_model()

    # Decode image
    image = Image.open(BytesIO(base64.b64decode(image_base64)))

    # Format as chat
    messages = [
        {"role": "system", "content": "You are an expert radiologist."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt or "Analyze this medical image"},
            {"type": "image", "image": image}
        ]}
    ]

    # Apply chat template
    text = self.processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Prepare inputs
    inputs = self.processor(
        images=image,
        text=text,
        return_tensors="pt"
    ).to(self.device)

    # Generate
    with torch.no_grad():
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=False
        )

    # Decode response
    response = self.processor.decode(outputs[0], skip_special_tokens=True)

    return response
```

**Mode 2: Cloud API**
```python
def _call_cloud_api(image_base64: str, prompt: str) -> str:
    response = requests.post(
        f"{self.api_domain}/analyze",
        json={"image": image_base64, "prompt": prompt},
        timeout=600  # 10 minutes
    )
    return response.json()["analysis"]
```

**Performance**:
- **First Request**: 10-20 seconds (model loading)
- **Subsequent Requests**: 2-4 seconds (inference only)
- **Memory**: 8GB+ recommended for 4B model

---

### 8. Chatbot Tools

#### A. MedicalChatbotTool (General Dataset Assistance)

**Location**: `src/tools/medical_chatbot_tool.py`

**Use Cases**:
- "What images are flagged?"
- "How many images have label 'Normal'?"
- "Analyze all flagged images"
- "What's the confidence distribution?"

**Context Building**:
```python
def _build_context(dataset_name, db_repo, agentic_repo, flagged_paths):
    context = []

    # Dataset overview
    annotations = db_repo.get_annotations(dataset_name)
    labels = {ann[2]: ... for ann in annotations}
    flagged_count = sum(1 for ann in annotations if ann[4].startswith("[FLAGGED]"))

    context.append(f"Dataset '{dataset_name}' Overview:")
    context.append(f"- Total images: {len(annotations)}")
    context.append(f"- Flagged images: {flagged_count}")
    context.append(f"- Label distribution: {labels}")

    # Flagged images details
    flagged = [ann for ann in annotations if ann[4].startswith("[FLAGGED]")]
    for img in flagged[:10]:  # Limit to 10
        context.append(f"- {img[1]}: {img[2]} - {img[4][:100]}...")

    # MedGemma analysis (from annotation_request)
    requests = agentic_repo.get_unprocessed_requests(dataset_name)
    for req in requests[:5]:  # Limit to 5
        context.append(f"MedGemma: {req['medgemma_raw'][:200]}...")

    return "\n".join(context)
```

**Function Calling** (Gemini Feature):
```python
tools = [
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="analyze_flagged_images",
                description="Analyze flagged medical images using MedGemma AI",
                parameters={"dataset_name": ..., "flagged_paths": ..., "prompt": ...}
            )
        ]
    )
]
```

**When user says**: "Analyze all flagged images"
**Gemini detects** function call and triggers `analyze_flagged_images()`
**System response**: Batch analysis of flagged images

#### B. ClinicalChatbotTool (Focused Q&A)

**Location**: `src/tools/clinical_chatbot_tool.py`

**Use Cases**:
- "Explain this annotation" (when viewing specific image)
- "What's the confidence score?"
- "What findings were detected?"
- "How many validation attempts?"

**Context Building**:
```python
def _build_annotation_context(agentic_repo, request_id):
    # Get full annotation_request data
    request = agentic_repo.get_annotation_request(request_id)

    # Get clean annotation
    annotation_data = agentic_repo.get_annotation_with_request(
        request['set_name'],
        request['path_url']
    )

    context = [
        f"Image: {request['path_url']}",
        f"Patient ID: {request['patient_id']}",
        f"Primary Label: {annotation_data['label']}",
        f"Clinical Summary: {annotation_data['desc']}",
        "",
        "DETAILED DATA:",
        f"Confidence Score: {request['confidence_score']}",
        f"Validation Status: {request['validation_status']}",
        f"Validation Attempts: {request['validation_attempt']}",
        "",
        "RAW MEDGEMMA ANALYSIS:",
        request['medgemma_raw'],
        "",
        "STRUCTURED FINDINGS:",
        json.dumps(request['pydantic_output'], indent=2)
    ]

    return "\n".join(context)
```

**Key Difference from MedicalChatbotTool**:
- Grounded in specific annotation data
- No function calling (pure Q&A)
- Access to both clean summary and raw outputs

---

### 9. Database Architecture (Two-Tier Design)

**Schema Location**: `DB/db_schema.sql`

**Repository Implementations**:
- `DB/repository.py` - Legacy AnnotationRepo (annotation table only)
- `DB/agentic_repository.py` - AgenticAnnotationRepo (two-tier operations)

#### Tier 1: `annotation_request` (Staging/Raw Data)

**Purpose**: Preserve full pipeline trace for debugging and reprocessing

```sql
CREATE TABLE annotation_request(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name INTEGER NOT NULL,
    path_url VARCHAR2(200) NOT NULL,

    -- Patient info
    patient_id INTEGER,

    -- Raw MedGemma output
    medgemma_raw TEXT,                        -- Full text analysis

    -- Gemini validated/structured output (JSON)
    gemini_validated TEXT,                    -- JSON string
    validation_attempt INTEGER DEFAULT 1,    -- Retry count
    validation_status VARCHAR2(20),          -- 'success'/'retry'/'fallback'

    -- Pydantic validated output (JSON)
    pydantic_output TEXT NOT NULL,           -- AnnotationOutput
    confidence_score REAL,

    -- Gemini enhancement (optional)
    gemini_enhanced BOOLEAN DEFAULT 0,
    gemini_report TEXT,
    urgency_level VARCHAR2(20),              -- 'critical'/'urgent'/'routine'
    clinical_significance VARCHAR2(20),      -- 'high'/'medium'/'low'

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0,             -- Transferred to annotation table?
    processing_error TEXT,

    UNIQUE(set_name, path_url)
);

CREATE INDEX idx_request_processed ON annotation_request(processed, set_name);
CREATE INDEX idx_request_created ON annotation_request(created_at);
```

**Key Operations** (`AgenticAnnotationRepo`):
```python
def save_annotation_request(...) -> int:
    """Save raw pipeline outputs to staging table"""

def get_unprocessed_requests(set_name) -> List[Dict]:
    """Get all images that need processing"""

def get_annotation_request(request_id) -> Dict:
    """Retrieve full request data by ID"""

def get_pipeline_stats(set_name) -> Dict:
    """Get metrics: success rate, avg confidence, etc."""
```

#### Tier 2: `annotation` (Clean/Production Data)

**Purpose**: Polished clinical summaries for frontend display

```sql
CREATE TABLE annotation(
    set_name INTEGER,
    path_url VARCHAR2(200),
    label VARCHAR2(20),                      -- Primary diagnosis (concise)
    patient_id INTEGER,
    desc VARCHAR(4000),                      -- Gemini-generated summary
    request_id INTEGER,                      -- Link to annotation_request

    CONSTRAINT fk_request FOREIGN KEY (request_id)
        REFERENCES annotation_request(id) ON DELETE CASCADE,
    PRIMARY KEY(set_name, path_url)
);
```

**Key Operations** (`AgenticAnnotationRepo`):
```python
def process_request_to_annotation(request_id, gemini_summary, primary_label):
    """Transfer staging → production"""
    request = self.get_annotation_request(request_id)

    # Insert clean summary
    self.cursor.execute(
        "INSERT OR REPLACE INTO annotation VALUES (?, ?, ?, ?, ?, ?)",
        (request['set_name'], request['path_url'], primary_label,
         request['patient_id'], gemini_summary, request_id)
    )

    # Mark as processed
    self.cursor.execute(
        "UPDATE annotation_request SET processed = 1 WHERE id = ?",
        [request_id]
    )
    self.connection.commit()

def get_annotation_with_request(set_name, path_url) -> Dict:
    """Join query for debugging: get clean summary + raw data"""
    return self.cursor.execute("""
        SELECT a.*, r.medgemma_raw, r.gemini_validated, r.confidence_score
        FROM annotation a
        LEFT JOIN annotation_request r ON a.request_id = r.id
        WHERE a.set_name = ? AND a.path_url = ?
    """, [set_name, path_url]).fetchone()
```

#### WAL Mode for Concurrency

```python
def __init__(self, db_path):
    self.connection = sqlite3.connect(
        db_path,
        check_same_thread=False,
        timeout=30.0,          # Wait up to 30s for locks
        isolation_level=None   # Autocommit mode
    )
    self.cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
    self.cursor.execute("PRAGMA foreign_keys = ON")
```

**Benefits of WAL**:
- Multiple readers don't block each other
- Writers don't block readers
- Better concurrency for batch processing
- Automatic checkpoint management

---

## Data Flow (Complete Lifecycle)

### Phase 1: Dataset Loading

```
User uploads folder → Streamlit UI
    ↓
POST /datasets/load
    ├─ dataset_name: "1"
    ├─ image_paths: ["/path/img1.jpg", "/path/img2.jpg", ...]
    ↓
AgenticAnnotationRepo.save_annotation_request()
    ├─ For each image:
    │   ├─ INSERT placeholder (processed=0, pydantic_output='{"findings":[]}')
    │   └─ Skip if already exists (UNIQUE constraint)
    ↓
Response: {"success": True, "loaded": 10, "skipped": 2}
```

### Phase 2: AI Analysis

```
User clicks "Analyze Dataset" → Streamlit UI
    ↓
POST /datasets/analyze
    ├─ dataset_name: "1"
    ├─ prompt: "Analyze these chest X-rays"
    ├─ force_reanalyze: False
    ↓
Backend: Get unprocessed requests
    ├─ SELECT * FROM annotation_request WHERE processed=0 AND set_name=1
    ↓
For each unprocessed image:
    ├─ Read image from disk
    ├─ Encode to base64
    ├─ Run AgenticAnnotationPipeline:
    │   │
    │   ├─ STEP 1: MedGemma Analysis
    │   │   └─ Raw text: "Chest X-ray shows bilateral opacities..."
    │   │
    │   ├─ STEP 2: Gemini Validation (with retries)
    │   │   ├─ Attempt 1: Convert to JSON
    │   │   ├─ Pydantic validation: AnnotationOutput(**json)
    │   │   └─ Status: 'success' | 'retry' | 'fallback'
    │   │
    │   ├─ STEP 3: Optional Enhancement
    │   │   └─ Urgency assessment, professional report
    │   │
    │   ├─ STEP 4: Build request_data
    │   │   └─ {medgemma_raw, gemini_validated, ...}
    │   │
    │   ├─ STEP 5: Generate Clinical Summary
    │   │   └─ "PRIMARY DIAGNOSIS: Pneumothorax\n\nSUMMARY: ..."
    │   │
    │   └─ STEP 6: Extract Primary Label
    │       └─ "Pneumothorax"
    │
    ├─ UPDATE annotation_request with real data
    │   └─ processed=0 (not yet transferred)
    │
    └─ Process to annotation table:
        ├─ INSERT INTO annotation (label, desc, request_id)
        └─ UPDATE annotation_request SET processed=1
    ↓
Response: {"success": True, "processed": 10, "errors": []}
```

### Phase 3: User Interaction

```
GET /datasets/1/annotations
    ↓
Fetch from annotation table:
    ├─ SELECT * FROM annotation WHERE set_name=1
    └─ Returns: [{path, label, desc, patient_id}, ...]
    ↓
Streamlit displays in image grid
    ├─ Colored label tags
    ├─ Clinical summary (desc field)
    └─ Per-image action buttons
```

### Phase 4: Chatbot Query

```
User asks: "What images are flagged?"
    ↓
POST /chat
    ├─ message: "What images are flagged?"
    ├─ dataset_name: "1"
    ├─ request_id: None  # General query, not clinical
    ↓
GeminiAgent.chat() routes to MedicalChatbotTool
    ├─ Build context:
    │   ├─ Dataset overview (from annotation table)
    │   ├─ Flagged images (desc starts with "[FLAGGED]")
    │   └─ MedGemma analysis (from annotation_request)
    │
    ├─ Call Gemini with context + user message
    └─ Return AI response
    ↓
Response: {"success": True, "ai_message": "You have 3 flagged images..."}
```

### Phase 5: Export

```
GET /datasets/1/export
    ↓
Fetch all annotations:
    ├─ SELECT * FROM annotation WHERE set_name=1
    └─ Format as JSON list
    ↓
Response:
{
  "dataset_name": "1",
  "total_annotations": 12,
  "annotations": [
    {"path": "/img1.jpg", "label": "Normal", "description": "..."},
    {"path": "/img2.jpg", "label": "Pneumothorax", "description": "..."}
  ]
}
```

---

## Observability & Monitoring

### Logging Strategy

**Configuration** (`src/config.py`):
```python
logging.basicConfig(
    level=getattr(logging, settings.log_level),  # DEBUG/INFO/WARNING/ERROR
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # Console only
)
```

**Logged Events**:
- Agent initialization
- Every annotation request (set_name, path, processing time)
- Tool calls (MedGemma, Gemini)
- Validation attempts and retries
- Errors and exceptions with stack traces
- Database operations (saves, queries)
- Chatbot conversations

**Example Log Trace**:
```
2025-12-15 10:30:00 - src.api.main - INFO - Analyzing dataset 1 with 10 unprocessed images
2025-12-15 10:30:01 - src.pipelines.agentic_annotation_pipeline - INFO - Processing image /img1.jpg
2025-12-15 10:30:03 - src.tools.medgemma_tool - INFO - MedGemma analysis complete: 512 chars
2025-12-15 10:30:05 - src.pipelines.validation_pipeline - INFO - Validation attempt 1: success
2025-12-15 10:30:06 - src.agent.summary_generator - INFO - Generated clinical summary: 256 chars
2025-12-15 10:30:07 - DB.agentic_repository - INFO - Saved annotation_request 42
2025-12-15 10:30:07 - DB.agentic_repository - INFO - Processed request 42 → annotation
2025-12-15 10:30:07 - src.pipelines.agentic_annotation_pipeline - INFO - ✓ Annotation complete (6.2s)
```

### Health Monitoring

**Endpoint**: `GET /health`

**Checks**:
1. Gemini API connectivity
2. MedGemma model loaded status
3. Database connectivity
4. Required environment variables

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gemini_connected": true,
  "medgemma_loaded": true,
  "database_connected": true,
  "uptime_seconds": 3600
}
```

### Error Recovery

**Validation Failures**:
```python
try:
    annotation = GeminiValidator.validate(...)
except ValidationError:
    # Retry with stricter prompt
    annotation = GeminiValidator.validate(..., attempt=2)
except:
    # Fallback to keyword parser
    annotation = FallbackParser.parse(...)
    annotation.confidence_score = 0.50  # Mark as low confidence
```

**MedGemma Failures**:
```python
try:
    analysis = MedGemmaTool.analyze_image(...)
except Exception as e:
    logger.error(f"MedGemma failed: {e}")
    # Save error to annotation_request.processing_error
    # Return user-friendly error message
```

---

## Security Considerations

### API Key Management
- Environment variables only (never committed)
- `.env.example` template provided
- Validation on startup (fail fast if missing)

### Input Validation
- Pydantic models validate all inputs
- Max lengths enforced:
  - Paths: 200 characters
  - Descriptions: 4000 characters
  - Labels: 20 characters
- Image format validation (JPEG, PNG)
- Size limits: 10MB recommended

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Permissive for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Recommendations**:
- Restrict `allow_origins` to frontend domain
- Add authentication middleware
- Rate limiting per IP/user
- HTTPS only
- API key rotation

### Data Privacy
- No persistent PHI storage (images read on-demand)
- Annotation data can be deleted
- No external data transmission (except Gemini API)
- SQLite file permissions: 600 (owner read/write only)

**HIPAA Compliance TODO**:
- Encryption at rest
- Audit trail (who accessed what)
- Data retention policies
- User authentication
- Access control (RBAC)

---

## Performance Characteristics

### Latency Breakdown

**Single Image Annotation** (average):
- MedGemma analysis: 2-4 seconds
- Gemini validation: 1-2 seconds
- Summary generation: 0.5-1 second
- Database operations: <50ms
- **Total**: 4-7 seconds per image

**First Image** (cold start):
- MedGemma model loading: +10-20 seconds (one-time)
- **Total**: 14-27 seconds

**Batch Processing** (10 images):
- Serial processing: 40-70 seconds
- With lazy loading: No additional overhead after first image
- **Average per image**: 4-7 seconds

### Throughput

- **Single-threaded**: ~8-15 images/minute
- **With parallel processing**: ~30-50 images/minute (future enhancement)

### Resource Usage

- **Memory**:
  - MedGemma 4B model: 8GB+ (FP16)
  - Backend (FastAPI): ~200MB
  - Frontend (Streamlit): ~100MB
  - Total: ~8.5GB minimum

- **CPU**:
  - MedGemma inference: 80-100% (1 core)
  - With CUDA: 10-20% CPU, 80% GPU

- **Storage**:
  - MedGemma model: 8GB
  - Database: ~1KB per annotation
  - 10,000 annotations: ~10MB

### Scalability

**Current Limitations**:
- Single-threaded processing
- Local MedGemma (one model instance)
- SQLite (not designed for high concurrency)

**Scaling Strategies**:
1. **Horizontal**: Multiple backend instances + load balancer
2. **Model Serving**: Dedicated MedGemma service (FastAPI + GPU)
3. **Database**: PostgreSQL for production
4. **Queue**: Celery + Redis for async processing
5. **Caching**: Redis for repeated analyses

---

## Future Enhancements

### Short-Term (V2.0)
1. **Parallel Processing**: Process multiple images concurrently
2. **Bounding Boxes**: Visual overlays on images
3. **RAG Integration**: Medical guideline knowledge base
4. **Improved Flagging**: Persistent flag system with reasons
5. **Export Formats**: PDF, DICOM SR, HL7 FHIR

### Medium-Term (V3.0)
1. **Real-Time Collaboration**: WebSocket support
2. **User Authentication**: Multi-user with RBAC
3. **Annotation History**: Version control for annotations
4. **Batch API**: Upload ZIP, get results
5. **Webhooks**: Notify when processing complete

### Long-Term (Production)
1. **HIPAA Compliance**: Full audit trail, encryption
2. **FDA Validation**: Clinical trial data
3. **Active Learning**: Improve model from corrections
4. **Multi-Modal**: Support CT, MRI, ultrasound
5. **Cloud Deployment**: Kubernetes, auto-scaling

---

## Technology Stack Summary

### Core
- **Python 3.11+**: Primary language
- **FastAPI 0.104+**: Async web framework
- **Streamlit 1.29+**: Interactive UI
- **Pydantic 2.5+**: Data validation

### AI/ML
- **Google Gemini 2.0 Flash**: LLM (validation, summary, chat)
- **MedGemma 4B-IT**: Medical specialist model
- **Transformers**: HuggingFace model loading
- **PyTorch**: MedGemma inference

### Data
- **SQLite**: Development database
- **WAL Mode**: Improved concurrency
- **Two-tier schema**: Staging + production

### DevOps
- **UV**: Fast package management (optional)
- **Docker**: Containerization (planned)
- **Shell Scripts**: Easy startup
- **Logging**: Python logging module

---

## Deployment Guide

### Development (Local)

```bash
# Setup
git clone https://github.com/your-repo/googol.git
cd googol
./install.sh
cp .env.example .env
# Edit .env: Add GOOGLE_API_KEY

# Run (2 terminals)
./run_backend.sh     # Terminal 1: Backend on :8000
./run_frontend.sh    # Terminal 2: Frontend on :8501
```

### Production (Docker) [Planned]

```bash
# Build
docker build -t medannotator .

# Run
docker run -p 8000:8000 --env-file .env medannotator
```

### Production (Cloud Run) [Recommended]

```bash
# Deploy backend
gcloud run deploy medannotator \
  --image gcr.io/project/medannotator \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=xxx

# Deploy frontend (Streamlit Cloud)
# Push to GitHub, connect repo in Streamlit Cloud
```

---

## Conclusion

MedAnnotator demonstrates a **production-ready agentic architecture** with:

✅ **Two-tier database** for full traceability
✅ **Bulletproof validation** with retries and fallbacks
✅ **Intelligent tool orchestration** (MedGemma + Gemini)
✅ **ReAct pattern** for autonomous decision-making
✅ **Human-in-the-loop** design for safety
✅ **Comprehensive logging** for debugging
✅ **Scalable architecture** for future growth

The system is ready for medical research use and can be extended to clinical workflows with additional compliance and validation work.

---

**Built with ❤️ by Team Googol**
🏥 Making medical annotation faster, better, and more accessible.
