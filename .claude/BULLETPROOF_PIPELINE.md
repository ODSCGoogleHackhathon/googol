# Bulletproof Annotation Pipeline

## 🎯 Overview

This implementation adds a **validation-first pipeline** that ensures all MedGemma outputs are bulletproofed through Gemini validation and Pydantic schema enforcement before reaching the database.

### Pipeline Flow

```
┌──────────────┐
│ Image (B64)  │
└──────┬───────┘
       │
       ↓
┌──────────────────────────┐
│  Step 1: MedGemma        │  ← Free (local model)
│  Raw medical analysis    │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│  Step 2: Gemini          │  ← ~$0.0005/image
│  Validator               │
│  • Structures JSON       │
│  • Retry logic (2x)      │
│  • Fallback parser       │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│  Step 3: Pydantic        │  ← No cost
│  Validation Gate         │
│  • Strict schema check   │
│  • Type validation       │
│  • Required fields       │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│  Step 4: Smart           │  ← No cost
│  Serialization           │
│  • JSON formatting       │
│  • Truncation (4000)     │
│  • Primary label extract │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│  SQLite Database         │
└──────────────────────────┘
```

### Optional Enhancement Layer

```
After Step 3 (if enabled):
┌──────────────────────────┐
│  Gemini Enhancement      │  ← ~$0.0015/image
│  • Generate report       │
│  • Assess urgency        │
│  • Quality check         │
└──────────────────────────┘
```

---

## 📁 New Files Created

### 1. **`src/pipelines/validation_pipeline.py`**
**Purpose:** Gemini-powered validation with retry logic

**Key Class:** `GeminiValidator`

**Features:**
- Converts MedGemma text → structured JSON using Gemini
- Two-stage validation prompt (initial + retry with stricter instructions)
- JSON schema enforcement
- Temperature 0.1 for consistent structured output

**Usage:**
```python
from src.pipelines.validation_pipeline import GeminiValidator

validator = GeminiValidator()
annotation_dict = validator.validate_and_structure(
    raw_analysis="Patient shows signs of pneumothorax...",
    patient_id="P-001",
    attempt=0
)
# Returns: {"patient_id": "P-001", "findings": [...], "confidence_score": 0.85, ...}
```

---

### 2. **`src/models/db_serializers.py`**
**Purpose:** Smart JSON truncation and DB format conversion

**Key Class:** `AnnotationSerializer`

**Features:**
- Converts `AnnotationOutput` → DB-ready dict
- Smart truncation (priorities: findings > gemini_metadata > additional_notes)
- VARCHAR2(20) label truncation
- Patient ID type conversion (str → int)

**Usage:**
```python
from src.models.db_serializers import AnnotationSerializer

serializer = AnnotationSerializer()
db_data = serializer.to_db_format(annotation, image_path="/path/to/img.jpg")
# Returns: {
#   "path": "/path/to/img.jpg",
#   "label": "Pneumothorax",
#   "patient_id": 0,
#   "desc": "{\"findings\": [...], \"confidence_score\": 0.85, ...}"
# }
```

**Truncation Strategy:**
- Max: 3900 chars (safety margin below 4000)
- Priority 1: Truncate `additional_notes` to 500 chars
- Priority 2: Truncate `gemini_report` to 800 chars
- Priority 3: Hard truncation at 3900

---

### 3. **`src/pipelines/annotation_pipeline.py`**
**Purpose:** Main orchestrator with retry and fallback logic

**Key Class:** `AnnotationPipeline`

**Features:**
- Orchestrates: MedGemma → Validation → (Enhancement) → Serialization
- Retry strategy: 2 validation attempts with Gemini, then fallback parser
- Exception handling at every step
- Optional Gemini enhancement integration

**Usage:**
```python
from src.pipelines.annotation_pipeline import AnnotationPipeline

pipeline = AnnotationPipeline(enhancer=None)  # Or pass GeminiEnhancer()
annotation, db_data = pipeline.annotate(
    image_base64="iVBORw0KGgo...",
    user_prompt="Analyze for fractures",
    patient_id="P-123",
    enable_enhancement=False,
    image_path="/data/xray_001.jpg"
)
# Returns: (AnnotationOutput, dict ready for DB)
```

---

## 🔧 Modified Files

### 1. **`src/agent/gemini_agent.py`**
**Changes:**
- Removed: Old local parser methods (`_create_smart_fallback_annotation`, `_generate_structured_annotation`)
- Added: Pipeline integration via `self.pipeline = AnnotationPipeline()`
- Simplified: `annotate_image()` now delegates to pipeline

**Before:**
```python
def annotate_image(self, image_base64, user_prompt, patient_id):
    medgemma_analysis = self.medgemma_tool.analyze_image(...)
    return self._create_smart_fallback_annotation(...)  # Local regex parser
```

**After:**
```python
def annotate_image(self, image_base64, user_prompt, patient_id, enable_enhancement=False):
    annotation, _ = self.pipeline.annotate(...)  # Bulletproof pipeline
    return annotation
```

---

### 2. **`src/api/main.py`**
**Changes:** Updated `/datasets/analyze` endpoint

**Before:**
```python
result = agent.annotate_image(image_base64, request.prompt)
primary_label = result.findings[0].label if result.findings else "No findings"
findings_json = json.dumps([f.dict() for f in result.findings])
desc = f"{findings_json}\n\n{result.additional_notes or ''}"[:500]  # 500 char limit!
db_repo.update_annotation(request.data_name, img_path, primary_label, desc)
```

**After:**
```python
annotation, db_data = agent.pipeline.annotate(
    image_base64=image_base64,
    user_prompt=request.prompt,
    patient_id=None,
    enable_enhancement=False,
    image_path=img_path,
)
db_repo.add_label(db_data["label"])
db_repo.add_patient(db_data["patient_id"], "Auto")
db_repo.update_annotation(request.data_name, img_path, db_data["label"], db_data["desc"])
```

**Benefits:**
- ✅ Pydantic validation ensures no malformed data reaches DB
- ✅ 4000 char limit (was 500)
- ✅ Smart truncation preserves critical fields
- ✅ Retry logic handles Gemini failures

---

## 🧪 Testing

### Quick Test (Imports & Serialization)
```bash
uv run python test_bulletproof_pipeline.py
```

**Expected Output:**
```
============================================================
BULLETPROOF PIPELINE TESTS
============================================================
Testing imports...
  ✓ GeminiValidator imported
  ✓ AnnotationSerializer imported
  ✓ AnnotationPipeline imported
  ✓ GeminiAnnotationAgent imported (refactored)

Testing AnnotationSerializer...
  ✓ Serialization works
    - Label: Pneumothorax
    - Desc length: 280 chars
    - Patient ID: 0

Testing Pydantic validation...
  ✓ Valid annotation passes
  ✓ Invalid confidence score rejected
  ✓ Invalid finding rejected

============================================================
✅ ALL TESTS PASSED
============================================================
```

### End-to-End Test (With Real Image)
```bash
# 1. Start backend
./run_backend.sh

# 2. In another terminal, test annotation
curl -X POST http://localhost:8000/annotate \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "...",
    "user_prompt": "Analyze this chest X-ray",
    "patient_id": "TEST-001",
    "enhance_with_gemini": false
  }'
```

**Monitor logs for:**
```
INFO:src.pipelines.annotation_pipeline:Pipeline Step 1: MedGemma analysis
INFO:src.pipelines.annotation_pipeline:Pipeline Step 2: Gemini validation
INFO:src.pipelines.validation_pipeline:✓ Gemini validation successful (attempt 1)
INFO:src.pipelines.annotation_pipeline:✓ Pipeline completed successfully: 2 findings, confidence=0.85
```

---

## 💰 Cost Analysis

### Per-Image Breakdown

**Validation Only (Default):**
- MedGemma: Free (local)
- Gemini validation: ~$0.0005
- **Total: ~$0.0005/image**

**With Enhancement (Optional):**
- MedGemma: Free
- Gemini validation: ~$0.0005
- Gemini enhancement: ~$0.0015
- **Total: ~$0.002/image**

### Budget Projections

| Mode | Cost/Image | $300 Budget | Images Supported |
|------|-----------|-------------|------------------|
| Validation Only | $0.0005 | $300 | **600,000** |
| Smart Enhancement (30% trigger) | $0.00095 | $300 | **315,000** |
| Full Enhancement | $0.002 | $300 | **150,000** |

**Recommendation:** Use "Validation Only" for MVP, add selective enhancement later.

---

## 🚨 Error Handling

### Retry Strategy

```
Attempt 1: Gemini validation with initial prompt
   ↓ (if fails)
Attempt 2: Gemini validation with stricter prompt
   ↓ (if fails)
Fallback: Local keyword-based parser
   ↓ (always succeeds with safe defaults)
```

### Error Scenarios

| Error Type | Handling | Fallback | Log Level |
|-----------|----------|----------|-----------|
| Gemini API timeout | Retry with backoff | Local parser | WARNING |
| Invalid JSON from Gemini | Retry with stricter prompt | Local parser | WARNING |
| Pydantic validation error | Log error, retry | Safe defaults | ERROR |
| MedGemma crash | Return error annotation | N/A | CRITICAL |

### Fallback Parser Behavior

When all Gemini attempts fail:
```python
# Fallback creates minimal safe annotation
AnnotationOutput(
    patient_id="FALLBACK-UNKNOWN",
    findings=[Finding(label="Analysis Incomplete", location="Overall", severity="Unknown")],
    confidence_score=0.3,  # Low confidence
    generated_by="MedGemma/Fallback",
    additional_notes="Fallback parser used. Original analysis: ..."
)
```

---

## 📊 Monitoring

### Key Metrics to Track

1. **Validation Success Rate**
   - Target: >95% on first attempt
   - Monitor: `grep "✓ Validation successful" logs/app.log | wc -l`

2. **Retry Rate**
   - Target: <10%
   - Monitor: `grep "Retrying with stricter" logs/app.log | wc -l`

3. **Fallback Usage**
   - Target: <1%
   - Monitor: `grep "Fallback parser used" logs/app.log | wc -l`

4. **Description Truncation**
   - Target: <5%
   - Monitor: `grep "Hard truncation required" logs/app.log | wc -l`

### Log Examples

**Success:**
```
INFO:src.pipelines.validation_pipeline:✓ Gemini validation successful (attempt 1)
INFO:src.pipelines.annotation_pipeline:✓ Pipeline completed successfully: 3 findings, confidence=0.92
```

**Retry:**
```
WARNING:src.pipelines.annotation_pipeline:⚠ Pydantic validation failed (attempt 1/2): confidence_score must be <= 1.0
INFO:src.pipelines.validation_pipeline:Retrying with stricter validation prompt...
INFO:src.pipelines.validation_pipeline:✓ Gemini validation successful (attempt 2)
```

**Fallback:**
```
WARNING:src.pipelines.annotation_pipeline:All Gemini validation attempts failed, using local fallback
WARNING:src.pipelines.annotation_pipeline:Using fallback parser due to error: ...
```

---

## 🔄 Migration Guide

### For Existing Data

If you already have annotations in the database with old format:

1. **Check current format:**
```sql
SELECT desc FROM annotation LIMIT 1;
```

2. **Old format** (simple string):
```
"Pneumothorax detected in right lung. Consolidation in left lung. ..."
```

3. **New format** (structured JSON):
```json
{
  "findings": [{"label": "Pneumothorax", "location": "Right lung", "severity": "Moderate"}],
  "confidence_score": 0.85,
  "generated_by": "MedGemma/Gemini",
  "additional_notes": "..."
}
```

**No migration needed** - new and old formats coexist. Frontend reads `desc` as-is.

---

## 🎓 Usage Examples

### Example 1: Basic Annotation
```python
from src.pipelines.annotation_pipeline import AnnotationPipeline
import base64

pipeline = AnnotationPipeline()

with open("chest_xray.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

annotation, db_data = pipeline.annotate(
    image_base64=image_b64,
    user_prompt="Analyze for pneumothorax",
    patient_id="P-12345",
    image_path="/data/chest_xray.jpg"
)

print(f"Findings: {len(annotation.findings)}")
print(f"Confidence: {annotation.confidence_score:.2f}")
print(f"Label for DB: {db_data['label']}")
```

### Example 2: With Enhancement
```python
from src.agent.gemini_enhancer import GeminiEnhancer

enhancer = GeminiEnhancer()
pipeline = AnnotationPipeline(enhancer=enhancer)

annotation, db_data = pipeline.annotate(
    image_base64=image_b64,
    enable_enhancement=True,  # Enable Gemini enhancement
    ...
)

print(f"Report: {annotation.gemini_report}")
print(f"Urgency: {annotation.urgency_level}")
print(f"Significance: {annotation.clinical_significance}")
```

### Example 3: API Endpoint Usage
```bash
# Analyze single image with validation
curl -X POST http://localhost:8000/annotate \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "'"$(base64 < image.jpg)"'",
    "user_prompt": "Detect fractures",
    "patient_id": "P-999"
  }'

# Analyze dataset (batch)
curl -X POST http://localhost:8000/datasets/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "data_name": "chest_xrays_2024",
    "prompt": "Analyze for abnormalities"
  }'
```

---

## 🛠️ Troubleshooting

### Issue: "Gemini validation failed: Invalid JSON"

**Cause:** Gemini returned non-JSON text

**Fix:** Retry logic handles this automatically (attempt 2 with stricter prompt)

**Manual Check:**
```python
from src.pipelines.validation_pipeline import GeminiValidator

validator = GeminiValidator()
result = validator.validate_and_structure(
    "Your MedGemma output here",
    patient_id="TEST",
    attempt=1  # Use stricter prompt
)
```

---

### Issue: "Pydantic ValidationError: confidence_score"

**Cause:** Gemini returned string "0.85" instead of float 0.85

**Fix:** Retry with stricter prompt (automatic)

**Manual Fix:**
```python
# In validation_pipeline.py, post-process if needed:
result["confidence_score"] = float(result["confidence_score"])
```

---

### Issue: "Description truncated at 3900 chars"

**Cause:** Total JSON exceeds 4000 char DB limit

**Solution:** This is expected and handled automatically. Check logs:
```
WARNING:src.models.db_serializers:Hard truncation required: 4234 -> 3900
```

**To reduce truncation:**
- Shorten `additional_notes` in MedGemma tool
- Reduce `gemini_report` verbosity
- Prioritize findings over narrative

---

## 📚 Next Steps

### Phase 2: Enhancement Integration (Post-MVP)

1. **Add selective enhancement triggers:**
```python
def should_enhance(annotation: AnnotationOutput) -> bool:
    # Low confidence
    if annotation.confidence_score < 0.7:
        return True

    # Critical findings
    critical_labels = ['pneumothorax', 'fracture', 'hemorrhage']
    if any(label.lower() in f.label.lower() for f in annotation.findings for label in critical_labels):
        return True

    return False
```

2. **Update analyze endpoint:**
```python
enable_enhancement = should_enhance(annotation)
annotation, db_data = agent.pipeline.annotate(..., enable_enhancement=enable_enhancement)
```

3. **Monitor cost:** Track Gemini API usage in logs

### Phase 3: Optimization

1. **Caching:** Implement response caching for similar images
2. **Batch processing:** Parallel Gemini calls for datasets
3. **Quality metrics:** Track validation success rates

---

## 📝 Summary

### What Was Achieved

✅ **Bulletproof validation** - Gemini + Pydantic double-check
✅ **Retry logic** - 2 attempts + fallback parser
✅ **Smart truncation** - 4000 chars with priority preservation
✅ **Cost-effective** - ~$0.0005/image for validation
✅ **Clean architecture** - Separate concerns (validate, serialize, enhance)
✅ **Zero database changes** - Works with existing schema
✅ **Backward compatible** - Old and new formats coexist

### Files Added
- `src/pipelines/validation_pipeline.py` (171 lines)
- `src/models/db_serializers.py` (152 lines)
- `src/pipelines/annotation_pipeline.py` (232 lines)
- `test_bulletproof_pipeline.py` (test suite)

### Files Modified
- `src/agent/gemini_agent.py` (refactored to use pipeline)
- `src/api/main.py` (updated /datasets/analyze endpoint)

### Total Implementation
- **~600 lines of production code**
- **~200 lines of tests**
- **15 hours estimated** ✅ **Completed in single session**

---

**Ready to rock! 🚀**
