# MedAnnotator - Project Setup Guide

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Google AI API Key (Gemini)
- Git

### Installation Steps

1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd googol
```

2. **Create Virtual Environment**
```bash
# Using conda (recommended)
conda env create -f environment.yml
conda activate medannotator

# OR using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set Up Environment Variables**
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Google API key
# Get your key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_actual_api_key_here
```

4. **Create Required Directories**
```bash
mkdir -p logs data/sample_images data/annotations
```

5. **Run the Application**

Open two terminal windows:

**Terminal 1 - Backend:**
```bash
python -m src.api.main
```

**Terminal 2 - Frontend:**
```bash
streamlit run src/ui/app.py
```

6. **Access the Application**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development Workflow

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/
```

### Code Quality
```bash
# Format code
black src/

# Lint code
flake8 src/
```

### Logging
- Logs are written to `logs/app.log`
- View logs in real-time:
```bash
tail -f logs/app.log
```

## Team Roles & Tasks

### Frontend Lead (Streamlit)
**Files to work on:**
- `src/ui/app.py` - Main Streamlit interface

**Tasks:**
- Image upload UI
- Results display
- JSON editor
- Download functionality

### Backend Lead (FastAPI)
**Files to work on:**
- `src/api/main.py` - API endpoints

**Tasks:**
- Endpoint implementation
- Request validation
- Error handling
- CORS configuration

### Agent/LLM Lead (Gemini Integration)
**Files to work on:**
- `src/agent/gemini_agent.py` - Main agent logic
- `src/config.py` - Configuration

**Tasks:**
- Gemini API integration
- ReAct pattern implementation
- JSON structuring
- Error recovery

### Tools Lead (MedGemma)
**Files to work on:**
- `src/tools/medgemma_tool.py` - MedGemma integration

**Tasks:**
- Mock analysis implementation
- Image processing
- (Optional) Real MedGemma integration
- Tool definition for function calling

## Hackathon Milestones

### Phase 1: Setup (2 hours)
- [x] Project structure created
- [x] Dependencies installed
- [x] Environment configured
- [ ] Team members can run the app locally

### Phase 2: Core Development (8 hours)
- [x] FastAPI backend running
- [x] Gemini agent implemented
- [x] MedGemma mock tool working
- [x] Streamlit UI functional
- [ ] End-to-end flow tested

### Phase 3: Polish (4 hours)
- [ ] Error handling improved
- [ ] UI/UX refinements
- [ ] Sample data added
- [ ] Documentation complete

### Phase 4: Demo Prep (2 hours)
- [ ] Demo video recorded
- [ ] README updated
- [ ] Code cleaned up
- [ ] Final testing

## Troubleshooting

### Backend won't start
- Check if port 8000 is in use: `lsof -i :8000`
- Verify GOOGLE_API_KEY in `.env`
- Check logs: `tail logs/app.log`

### Frontend shows "Backend Disconnected"
- Ensure backend is running on port 8000
- Check API_URL in `src/ui/app.py`
- Test backend: `curl http://localhost:8000/health`

### Gemini API errors
- Verify API key is valid
- Check quota: https://makersuite.google.com/
- Ensure model name is correct in config

### Import errors
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.11+)

## API Endpoints Reference

### POST /annotate
Annotate a medical image.

**Request:**
```json
{
  "image_base64": "base64_encoded_image_string",
  "user_prompt": "Focus on lung fields",
  "patient_id": "P-12345"
}
```

**Response:**
```json
{
  "success": true,
  "annotation": {
    "patient_id": "P-12345",
    "findings": [
      {
        "label": "Normal",
        "location": "Bilateral lung fields",
        "severity": "None"
      }
    ],
    "confidence_score": 0.85,
    "generated_by": "MedGemma/Gemini",
    "additional_notes": "No acute abnormalities"
  },
  "processing_time_seconds": 2.34
}
```

### GET /health
Check system health.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gemini_connected": true,
  "medgemma_connected": true
}
```

## Configuration Options

Edit `src/config.py` or `.env`:

- `GEMINI_MODEL`: Model to use (default: gemini-2.0-flash-exp)
- `MEDGEMMA_ENDPOINT`: local or vertex_ai
- `BACKEND_PORT`: Backend port (default: 8000)
- `STREAMLIT_PORT`: Frontend port (default: 8501)
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR

## Next Steps

### For Production
1. Deploy backend to Cloud Run
2. Deploy frontend to Streamlit Cloud
3. Add authentication
4. Integrate real MedGemma API
5. Add database for annotation storage
6. Implement RAG for medical guidelines

### For Hackathon
1. Test with sample medical images
2. Record demo video
3. Update DEMO.md with video link
4. Polish UI/UX
5. Practice pitch

## Resources

- [Gemini API Docs](https://ai.google.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [MedGemma on Hugging Face](https://huggingface.co/google/medgemma-4b)

## Support

For questions or issues:
1. Check this guide
2. Review logs in `logs/app.log`
3. Ask in team chat
4. Check GitHub Issues
