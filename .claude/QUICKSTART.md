# MedAnnotator - Quick Start Guide

## What is MedAnnotator?

MedAnnotator is an **AI-powered medical image annotation tool** that uses Google Gemini and MedGemma to provide fast, structured, and consistent annotations for medical images (X-rays, CT scans, MRIs).

**Built by Team Googol for the Agentic AI App Hackathon**

## 🚀 5-Minute Setup

### 1. Prerequisites
- Python 3.11+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### 2. Installation
```bash
# Clone the repo
git clone <your-repo-url>
cd googol

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
./run_backend.sh
# or: python -m src.api.main
```

**Terminal 2 - Frontend:**
```bash
./run_frontend.sh
# or: streamlit run src/ui/app.py
```

### 4. Access the App
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000/docs

## 📖 How to Use

1. **Upload** a medical image (JPG/PNG)
2. **Add** optional patient ID and instructions
3. **Click** "Annotate Image"
4. **Review** the AI-generated structured findings
5. **Edit** the JSON if needed
6. **Download** the annotation

## 🏗️ Architecture Overview

```
Streamlit UI → FastAPI Backend → Gemini Agent → MedGemma Tool
                                      ↓
                              Structured JSON Output
```

**Agentic Features:**
- **ReAct Pattern**: Reasoning + Acting workflow
- **Tool Orchestration**: Automatic MedGemma → Gemini pipeline
- **Structured Output**: Consistent JSON every time
- **Error Recovery**: Graceful fallbacks
- **Logging**: Full trace of decisions

## 📁 Project Structure

```
googol/
├── src/
│   ├── api/              # FastAPI backend
│   ├── agent/            # Gemini agent (ReAct)
│   ├── tools/            # MedGemma tool
│   ├── ui/               # Streamlit frontend
│   ├── config.py         # Configuration
│   └── schemas.py        # Data models
├── data/
│   ├── sample_images/    # Test images
│   └── annotations/      # Output annotations
├── logs/                 # Application logs
├── ARCHITECTURE.md       # System architecture
├── EXPLANATION.md        # Technical details
├── DEMO.md              # Demo video
└── README.md            # This file
```

## 🎯 Key Features

### For Users
- ✅ Fast annotation (2-5 seconds)
- ✅ Structured JSON output
- ✅ Editable results
- ✅ Downloadable annotations
- ✅ Confidence scores
- ✅ Human-in-the-loop design

### For Developers
- ✅ Clean architecture
- ✅ Comprehensive logging
- ✅ Error handling
- ✅ Type validation (Pydantic)
- ✅ API documentation (FastAPI)
- ✅ Extensible tool system

## 🔧 Configuration

Edit `.env` or `src/config.py`:

```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional
GEMINI_MODEL=gemini-2.0-flash-exp
BACKEND_PORT=8000
STREAMLIT_PORT=8501
LOG_LEVEL=INFO
```

## 📊 Example Output

```json
{
  "patient_id": "P-12345",
  "findings": [
    {
      "label": "Pneumothorax",
      "location": "Right lung apex",
      "severity": "Small"
    }
  ],
  "confidence_score": 0.85,
  "generated_by": "MedGemma/Gemini",
  "additional_notes": "No other acute abnormalities"
}
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Verify API key is set
cat .env | grep GOOGLE_API_KEY

# Check logs
tail -f logs/app.log
```

### Frontend shows "Backend Disconnected"
```bash
# Test backend health
curl http://localhost:8000/health

# Restart backend
./run_backend.sh
```

### Gemini API errors
- Verify API key is valid
- Check quota at https://makersuite.google.com/
- Ensure model name is correct

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and components
- **[EXPLANATION.md](EXPLANATION.md)** - Technical deep dive
- **[PROJECT_SETUP.md](PROJECT_SETUP.md)** - Detailed setup instructions
- **[TEAM_TASKS.md](TEAM_TASKS.md)** - Task distribution
- **[DEMO_GUIDE.md](DEMO_GUIDE.md)** - Demo video script

## 🎓 Judging Criteria Alignment

### Technical Excellence ⭐⭐⭐⭐⭐
- Robust error handling
- Comprehensive logging
- Clean code architecture
- Type safety with Pydantic
- Async API design

### Solution Architecture ⭐⭐⭐⭐⭐
- Clear component separation
- Modular design
- Extensive documentation
- Easy to maintain and extend

### Innovative Gemini Integration ⭐⭐⭐⭐⭐
- Gemini 2.0 Flash with JSON mode
- ReAct reasoning pattern
- Multi-model orchestration
- Structured output enforcement
- Tool calling architecture

### Societal Impact & Novelty ⭐⭐⭐⭐⭐
- Solves real medical problem
- Improves radiology workflow efficiency
- Enables better research datasets
- Human-in-the-loop design
- Scalable to thousands of images

## 🤝 Team Googol

- Rafael Kovashikawa (rkovashikawa@gmail.com) - GitHub: kovashikawa
- Ravali Yerrapothu (yravali592@gmail.com) - GitHub: ry639a
- Tyrone
- Guilherme (guirque@gmail.com) - GitHub: guirque

## 📝 License

See [LICENSE](LICENSE) file.

## ⚠️ Disclaimer

**This tool is for research and educational purposes only.**
- NOT FDA approved
- NOT for clinical diagnosis
- Requires physician oversight
- May contain PHI concerns

## 🚀 Next Steps

1. ✅ Set up local environment
2. ✅ Run the application
3. ✅ Upload a test image
4. ✅ Review the output
5. ⏭️ Record demo video
6. ⏭️ Submit to hackathon

## 📞 Support

- Technical questions: Check [PROJECT_SETUP.md](PROJECT_SETUP.md)
- Architecture questions: Check [ARCHITECTURE.md](ARCHITECTURE.md)
- Issues: Open a GitHub issue
- Team chat: [Your team communication channel]

---

**Built with ❤️ using Google Gemini, FastAPI, and Streamlit**
