#!/bin/bash
# Run the Streamlit frontend for MedAnnotator

echo "🚀 Starting MedAnnotator Frontend..."
uv run streamlit run src/ui/app.py --server.port=8501
