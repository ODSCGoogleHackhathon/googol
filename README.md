# MedAnnotator

> **AI-Powered Medical Image Annotation Tool**
> Built by Team Googol for the Agentic AI App Hackathon
>
> 🏆 **2nd Place Winner** - ODSC Agentic AI App Hackathon 2024
> [Official Announcement](https://www.linkedin.com/feed/update/urn:li:activity:7407900037394984960/)

[![CI](https://github.com/your-repo/googol/workflows/MedAnnotator%20CI/badge.svg)](https://github.com/your-repo/googol/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Hackathon](https://img.shields.io/badge/ODSC%20Hackathon-2nd%20Place-gold.svg)](https://www.linkedin.com/feed/update/urn:li:activity:7407900037394984960/)

## Overview

MedAnnotator is an LLM-assisted multimodal medical image annotation tool that uses Google Gemini and MedGemma to provide fast, structured, and consistent annotations for medical images (X-rays, CT scans, MRIs).

**Key Innovation**: Implements a **ReAct (Reasoning + Acting)** agentic pattern where the system autonomously reasons about medical images, orchestrates specialized tools, and generates standardized JSON outputs.

### Why MedAnnotator?

- **Problem**: Manual medical image annotation is slow (hours per image), inconsistent, and doesn't scale
- **Solution**: AI-powered structured annotation in 2-5 seconds
- **Impact**: Faster radiology workflows, better research datasets, improved patient care

## ✨ What's New

### Latest Developments

**Cloud API Integration** (December 2024)
- ☁️ MedGemma now deployable on Google Cloud Compute Engine
- 🔄 Automatic fallback: Cloud API → Local HuggingFace model
- ⚡ Faster processing without local GPU requirements
- 📖 See [CLOUD_API_INTEGRATION.md](CLOUD_API_INTEGRATION.md) for setup

**Two-Tier Agentic Architecture**
- 🧠 Enhanced agent pipeline with retry logic and validation
- 💾 Dual database tables for full traceability (`annotation_request` + `annotation`)
- 🤖 Medical chatbot with dataset context and tool calling
- 📊 Real-time analytics and flagged image tracking

**Demo & Documentation**
- 🎬 Complete demo video with timestamp navigation ([DEMO.md](DEMO.md))
- 📚 Comprehensive technical documentation
- 🏆 2nd Place in ODSC Agentic AI App Hackathon 2024

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- (Optional but recommended) [UV](https://github.com/astral-sh/uv) for 10x faster installation

### Installation

**Option 1: With UV (Recommended - 10x faster)** ⚡

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Clone and setup
git clone https://github.com/your-username/googol.git
cd googol

# One-command install
./install.sh

# Or manually
uv sync

# Set up environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

**Option 2: With pip (Traditional)**

```bash
# Clone the repository
git clone https://github.com/your-username/googol.git
cd googol

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

> 💡 **New to UV?** See [.claude/UV_SETUP.md](.claude/UV_SETUP.md) for a complete guide!

### Running the Application

**With Scripts (Auto-detects UV or Python):**

```bash
# Terminal 1 - Backend
chmod +x run_backend.sh run_frontend.sh
./run_backend.sh

# Terminal 2 - Frontend
./run_frontend.sh
```

**With UV Directly (No activation needed!):**

```bash
# Terminal 1 - Backend
uv run python -m src.api.main

# Terminal 2 - Frontend
uv run streamlit run src/ui/app.py
```

**With Traditional Python:**

```bash
# Activate venv first
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Terminal 1 - Backend
python -m src.api.main

# Terminal 2 - Frontend
streamlit run src/ui/app.py
```

**Access:**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000/docs

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t medannotator .
docker run -p 8000:8000 --env-file .env medannotator
```

## 📋 Features

### Agentic Capabilities
- ✅ **ReAct Pattern**: Multi-step reasoning (Plan → Act → Observe → Structure)
- ✅ **Tool Orchestration**: Automatic MedGemma → Gemini pipeline
- ✅ **Autonomous Decision Making**: Plans annotation strategy independently
- ✅ **Error Recovery**: Graceful fallbacks and comprehensive logging
- ✅ **Structured Output**: Consistent JSON schema enforcement

### Core Features
- ✅ Medical image upload (JPG, PNG)
- ✅ AI-powered image analysis (2-5 second processing)
- ✅ Structured JSON annotation output
- ✅ Editable results with confidence scores
- ✅ Downloadable annotations
- ✅ Human-in-the-loop design

### Technical Features
- ✅ FastAPI async backend
- ✅ Streamlit interactive frontend
- ✅ Pydantic data validation
- ✅ Comprehensive error handling
- ✅ Full logging and observability
- ✅ Docker containerization
- ✅ CI/CD pipeline

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend (UI)                      │
│              Image Upload → Results Display → Edit              │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (API)                       │
│            /annotate endpoint → Request Validation              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  GeminiAnnotationAgent (ReAct)                  │
│  Reason → Act (MedGemma) → Observe → Structure (Gemini)        │
└─────────────┬────────────────────────────────┬──────────────────┘
              │                                │
              ▼                                ▼
    ┌──────────────────┐           ┌──────────────────────┐
    │  MedGemma Tool   │           │    Gemini API        │
    │ Medical Analysis │           │  JSON Structuring    │
    └──────────────────┘           └──────────────────────┘
```

**See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.**

## 🎯 Example Output

```json
{
  "patient_id": "P-12345",
  "findings": [
    {
      "label": "Pneumothorax",
      "location": "Right lung apex",
      "severity": "Small"
    },
    {
      "label": "Normal",
      "location": "Cardiac silhouette",
      "severity": "None"
    }
  ],
  "confidence_score": 0.85,
  "generated_by": "MedGemma/Gemini-2.0-Flash",
  "additional_notes": "No other acute abnormalities identified"
}
```

## 📂 Project Structure

```
googol/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline
├── .claude/                    # Additional documentation
│   ├── PROJECT_SETUP.md        # Detailed setup guide
│   ├── QUICKSTART.md           # 5-minute guide
│   ├── TEAM_TASKS.md           # Task distribution
│   └── DEMO_GUIDE.md           # Demo preparation
├── src/
│   ├── api/                    # FastAPI backend
│   │   └── main.py             # API endpoints
│   ├── agent/                  # Gemini agent (ReAct)
│   │   └── gemini_agent.py     # Orchestration logic
│   ├── tools/                  # Tool integrations
│   │   └── medgemma_tool.py    # MedGemma wrapper
│   ├── ui/                     # Streamlit frontend
│   │   └── app.py              # UI application
│   ├── config.py               # Configuration
│   └── schemas.py              # Data models
├── data/
│   ├── sample_images/          # Test images
│   └── annotations/            # Output annotations
├── logs/                       # Application logs
├── tests/                      # Test suite
├── ARCHITECTURE.md             # System architecture ⭐
├── EXPLANATION.md              # Technical explanation ⭐
├── DEMO.md                     # Demo video link ⭐
├── TEST.sh                     # Smoke test script ⭐
├── Dockerfile                  # Docker configuration ⭐
├── docker-compose.yml          # Docker Compose config
├── requirements.txt            # Python dependencies
├── environment.yml             # Conda environment
└── README.md                   # This file ⭐
```

⭐ = Required for hackathon submission

## 🧪 Testing

Run the smoke test suite:

```bash
chmod +x TEST.sh
./TEST.sh
```

This will verify:
- Python version compatibility
- Required dependencies
- Module imports
- Configuration loading
- Mock tool functionality
- Documentation completeness

## 📚 Documentation

### Core Documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture with diagrams
- **[EXPLANATION.md](EXPLANATION.md)** - Technical deep dive and workflows
- **[DEMO.md](DEMO.md)** - Demo video with detailed timestamps (3:09 minutes)
- **[CLOUD_API_INTEGRATION.md](CLOUD_API_INTEGRATION.md)** - Cloud MedGemma API setup and deployment

### Setup Guides
- **[.claude/PROJECT_SETUP.md](.claude/PROJECT_SETUP.md)** - Detailed setup instructions
- **[.claude/QUICKSTART.md](.claude/QUICKSTART.md)** - 5-minute quick start
- **[.claude/MEDGEMMA_SETUP.md](.claude/MEDGEMMA_SETUP.md)** - MedGemma model configuration

## 🏆 Hackathon Criteria

### ✅ Technical Excellence
- Production-quality code (900+ lines)
- Comprehensive error handling
- Full logging and observability
- Type safety with Pydantic
- Async API design

### ✅ Solution Architecture & Documentation
- Clear component separation
- Modular, maintainable design
- 2000+ lines of documentation
- ASCII architecture diagrams
- Complete technical explanations

### ✅ Innovative Gemini Integration
- **Gemini 2.0 Flash** with JSON mode
- **ReAct pattern** for agentic behavior
- **Multi-model orchestration** (Gemini + MedGemma)
- **Structured output enforcement**
- **Tool calling architecture**

### ✅ Societal Impact & Novelty
- Solves real radiology workflow problem
- Improves annotation consistency
- Enables better medical research
- Scalable to thousands of images
- Human-in-the-loop design for safety

## 🎬 Demo

📺 **[Watch the Demo Video (3:09)](https://docs.google.com/videos/d/1h6Elcmftgcl6Z3IzYGaVDPj4N1RUVWn96Nyir-YX6bM/edit?usp=sharing)** | **[Detailed Timestamps & Analysis](DEMO.md)**

Watch our complete walkthrough showing:
- Problem statement and solution overview
- Dataset loading and configuration
- AI chatbot interaction with tool calling
- MedGemma analysis and Gemini validation pipeline
- Real-time structured output generation
- Edge case handling and human-in-the-loop design
- Real-world impact

## 🤝 Team Googol

🏆 **2nd Place Winners** - ODSC Agentic AI App Hackathon 2024

- **Rafael Kovashikawa** - [@kovashikawa](https://github.com/kovashikawa)
- **Ravali Yerrapothu** - [@ry639a](https://github.com/ry639a)
- **Tyrone**
- **Guilherme** - [@guirque](https://github.com/guirque)

**Recognition**: [Official ODSC LinkedIn Announcement](https://www.linkedin.com/feed/update/urn:li:activity:7407900037394984960/)

## 🛠️ Technology Stack

### Core
- **Python 3.11** - Primary language
- **FastAPI** - High-performance async web framework
- **Streamlit** - Interactive web UI
- **Pydantic** - Data validation and settings

### AI/ML
- **Google Gemini 2.0 Flash** - LLM reasoning and JSON generation
- **MedGemma 4B-IT** - Medical specialist model
  - Deployment: HuggingFace (local) or Google Cloud Compute Engine (cloud)
  - Automatic fallback for reliability
- **google-generativeai** - Gemini SDK
- **transformers** - HuggingFace model loading
- **PyTorch** - Deep learning framework

### Cloud & Infrastructure
- **Google Cloud Compute Engine** - Cloud MedGemma deployment
- **Docker** - Containerization
- **GitHub Actions** - CI/CD
- **Uvicorn** - ASGI server
- **SQLite** - Two-tier database architecture

## ⚠️ Important Notes

### Disclaimer
**This tool is for research and educational purposes only.**
- NOT FDA approved
- NOT for clinical diagnosis
- Requires physician oversight
- May contain PHI concerns - anonymize data before upload

### Current Limitations
- MedGemma uses mock data (real integration via Vertex AI possible)
- Stateless design (no annotation history)
- Single-user sessions
- Max image size: 10MB recommended

See [EXPLANATION.md](EXPLANATION.md) for detailed limitations and future enhancements.

## 🔮 Future Roadmap

### V2.0 (Post-Hackathon)
- Real MedGemma integration via Vertex AI
- RAG with medical guidelines
- Bounding box visualization
- Annotation history database
- User authentication

### V3.0 (Production)
- HIPAA compliance
- FDA validation pathway
- Multi-user collaboration
- Batch processing
- Export to DICOM SR / HL7 FHIR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini Team for the powerful API
- MedGemma researchers for the specialized medical model
- FastAPI and Streamlit communities
- Agentic AI App Hackathon organizers

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/your-username/googol/issues)
- **Email**: rkovashikawa@gmail.com
- **Documentation**: See [.claude/](.claude/) folder for additional guides

---

**Built with ❤️ using Google Gemini, FastAPI, and Streamlit**

🏥 Making medical annotation faster, better, and more accessible.
