#!/bin/bash
# Script to run the Streamlit frontend

echo "Starting MedAnnotator Frontend..."
echo "================================="
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "WARNING: Backend does not appear to be running!"
    echo "Please start the backend first:"
    echo "  ./run_backend.sh"
    echo ""
    echo "Continuing anyway..."
    echo ""
fi

# Run the frontend
echo "Starting frontend on http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Use uv if available, otherwise fall back to streamlit
if command -v uv &> /dev/null; then
    echo "Using uv to run frontend..."
    uv run streamlit run src/ui/app.py
else
    echo "Using streamlit to run frontend..."
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
        echo "WARNING: No virtual environment detected."
        echo "Consider installing uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo ""
    fi
    streamlit run src/ui/app.py
fi
