# Flag Feature Implementation Summary

## Overview
Successfully implemented a robust flagging system that allows users to flag medical images for review. Flags are stored in a dedicated `flagged` boolean column in the `annotation_request` table and persist through the entire annotation lifecycle.

## What Was Changed

### 1. Database Schema ([DB/db_schema.sql](DB/db_schema.sql))
Added `flagged` column to `annotation_request` table:
```sql
flagged BOOLEAN DEFAULT 0,  -- User-flagged for review/attention
```

**Location:** Line 49

### 2. Database Repository ([DB/agentic_repository.py](DB/agentic_repository.py))
Added two new methods:

#### `flag_annotation(set_name, path_url, flagged=True)` (Lines 359-409)
- Flags or unflags an annotation
- **Smart placeholder creation**: If an image is flagged before being analyzed, creates a minimal `annotation_request` placeholder
- Handles both existing and non-existing annotation_request entries
- Returns `True` on success, `False` if unflagging non-existent entry

#### `get_flagged_requests(set_name)` (Lines 411-418)
- Retrieves all flagged annotation requests for a dataset
- Returns list of dicts with full request data (path, patient_id, confidence_score, etc.)

### 3. API Schemas ([src/schemas.py](src/schemas.py))
Added two new Pydantic models (Lines 136-149):

```python
class FlagAnnotationRequest(BaseModel):
    img: str
    data_name: str
    flagged: bool = True

class FlagAnnotationResponse(BaseModel):
    success: bool
    message: str
    flagged: bool
```

### 4. API Endpoint ([src/api/main.py](src/api/main.py))
Added new endpoint `PATCH /annotations/flag` (Lines 426-453):
- Accepts dataset name, image path, and flag status
- Calls `agentic_repo.flag_annotation()`
- Returns 404 if annotation not found (only when unflagging)
- Returns 400 for invalid dataset name
- Returns 500 for server errors

### 5. API Client ([src/ui/api_client.py](src/ui/api_client.py))
Added `flag_annotation()` function (Lines 103-119):
- Sends PATCH request to `/annotations/flag`
- 10-second timeout
- Returns success/error dict

### 6. UI Component ([src/ui/components/image.py](src/ui/components/image.py))
Updated Flag button handler (Lines 21-28):
- Replaced old method (adding `[FLAGGED]` prefix to description)
- Now calls `api_client.flag_annotation()` directly
- Shows spinner during operation
- Displays success message: "⚠️ Flagged for review!"
- Shows error message if operation fails

### 7. Chatbot Integration ([src/tools/medical_chatbot_tool.py](src/tools/medical_chatbot_tool.py))
Updated `_get_flagged_images()` method (Lines 76-104):
- **Old behavior**: Checked for `[FLAGGED]` prefix in annotation.desc field
- **New behavior**: Queries `annotation_request.flagged` column via `agentic_repo.get_flagged_requests()`
- Returns cleaner data structure with request_id, confidence_score, and validation_status

Also updated calls to `_get_flagged_images()`:
- Line 194: Changed from `db_repo` to `agentic_repo`
- Line 273: Changed from `db_repo` to `repo` (which is agentic_repo)
- Lines 181-187: Updated flagged count calculation to use `agentic_repo.get_flagged_requests()`

## Key Features

### ✅ Flag Persistence
Flags persist through the entire annotation lifecycle:
1. Image loaded → Can be flagged (creates placeholder)
2. Image analyzed → Flag remains on annotation_request
3. Request processed to annotation table → Flag still persists
4. Re-analysis triggered → Flag remains unchanged

### ✅ Smart Placeholder Creation
When flagging an image that hasn't been analyzed yet:
- Creates minimal `annotation_request` entry automatically
- Only includes required fields: `set_name`, `path_url`, `pydantic_output`, `flagged`
- Prevents errors from missing annotation_request entries
- Allows users to flag images immediately upon upload

### ✅ Chatbot Function Calling
The AI chatbot can:
- Detect "analyze flagged images" intent
- Retrieve all flagged images using `_get_flagged_images()`
- Trigger analysis via direct pipeline call (no HTTP recursion)
- Process only unprocessed flagged images by default

## Migration Guide

### For New Databases
Simply initialize with the updated schema:
```bash
sqlite3 DB/annotations.db < DB/db_schema.sql
```

### For Existing Databases
Use the migration script:
```bash
sqlite3 DB/annotations.db < DB/migrate_add_flagged.sql
```

The migration script:
1. Adds `flagged` column to `annotation_request`
2. Creates index for faster flagged queries
3. Migrates existing `[FLAGGED]` prefixes (optional)
4. Can clean up old prefixes from descriptions (optional, commented out)

## Testing

### Automated Tests
Run comprehensive test suite:
```bash
uv run python test_flag_feature.py
```

Tests verify:
- ✓ Flagged column exists in schema
- ✓ Flag/unflag operations work
- ✓ Flags persist after processing
- ✓ Multiple flagged images handled correctly
- ✓ Chatbot retrieves flagged images
- ✓ Placeholder creation for non-analyzed images
- ✓ Unflagging works correctly

### Manual Testing
1. Start backend: `./run_backend.sh`
2. Start frontend: `./run_frontend.sh`
3. Upload images to a dataset
4. Click "Flag" button on any image
5. Verify flag appears immediately
6. Analyze the dataset
7. Verify flag persists after analysis
8. Ask chatbot to "analyze flagged images"
9. Verify chatbot processes only flagged images

## API Usage Examples

### Flag an image
```bash
curl -X PATCH http://localhost:8000/annotations/flag \
  -H "Content-Type: application/json" \
  -d '{
    "data_name": "1",
    "img": "/path/to/image.jpg",
    "flagged": true
  }'
```

### Unflag an image
```bash
curl -X PATCH http://localhost:8000/annotations/flag \
  -H "Content-Type: application/json" \
  -d '{
    "data_name": "1",
    "img": "/path/to/image.jpg",
    "flagged": false
  }'
```

### Get flagged images (via chatbot)
Ask the chatbot: "What images are flagged?" or "Analyze all flagged images"

## Error Handling

| Error Code | Cause | Solution |
|------------|-------|----------|
| 400 | Invalid dataset name (not integer) | Ensure dataset name is numeric |
| 404 | Trying to unflag non-existent request | This is expected, no action needed |
| 500 | Database error or server issue | Check logs, verify database connection |
| 503 | Agentic repository not initialized | Restart backend |

## Files Modified

### Core Implementation
- [DB/db_schema.sql](DB/db_schema.sql) - Added `flagged` column
- [DB/agentic_repository.py](DB/agentic_repository.py) - Added flag methods
- [src/schemas.py](src/schemas.py) - Added flag request/response models
- [src/api/main.py](src/api/main.py) - Added flag endpoint
- [src/ui/api_client.py](src/ui/api_client.py) - Added flag API client
- [src/ui/components/image.py](src/ui/components/image.py) - Updated UI flag button
- [src/tools/medical_chatbot_tool.py](src/tools/medical_chatbot_tool.py) - Updated flag detection

### Supporting Files
- [DB/migrate_add_flagged.sql](DB/migrate_add_flagged.sql) - Migration script for existing DBs
- [test_flag_feature.py](test_flag_feature.py) - Comprehensive test suite

## Benefits

1. **Clean Architecture**: Flags stored in proper database column, not string prefix
2. **Persistent State**: Flags survive re-analysis and processing
3. **Immediate Flagging**: Users can flag images before analysis
4. **AI Integration**: Chatbot can detect and process flagged images
5. **Better Performance**: Database queries instead of string parsing
6. **Type Safety**: Boolean column instead of string checking
7. **Scalability**: Indexed column for fast flagged image retrieval

## Troubleshooting

### Flag button shows error
1. Check backend logs for detailed error message
2. Verify database has `flagged` column: `sqlite3 DB/annotations.db "PRAGMA table_info(annotation_request)"`
3. Ensure backend was restarted after migration

### Flagged images not showing in chatbot
1. Verify flags exist: `sqlite3 DB/annotations.db "SELECT path_url, flagged FROM annotation_request WHERE flagged=1"`
2. Check chatbot is using `agentic_repo`, not old `db_repo`
3. Ensure dataset name is correct (integer)

### Old [FLAGGED] prefixes still visible
Run migration cleanup (uncomment lines in migrate_add_flagged.sql):
```sql
UPDATE annotation
SET desc = SUBSTR(desc, 11)
WHERE desc LIKE '[FLAGGED]%';
```

## Future Enhancements

Potential improvements:
- Add flag timestamp (when was it flagged?)
- Add flag reason/notes (why was it flagged?)
- Add flag priority levels (high/medium/low)
- Add bulk flag operations (flag all with confidence < 0.8)
- Add flag filters in UI (show only flagged, show only unflagged)
- Add flag statistics in dashboard
- Add flag notifications for clinical team

## Conclusion

The flag feature is fully functional and production-ready. Images can be flagged at any stage of the annotation lifecycle, flags persist through re-analysis, and the AI chatbot can intelligently process flagged images on demand.
