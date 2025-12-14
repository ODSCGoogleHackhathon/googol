#!/bin/bash
# Script to run the FastAPI backend

echo "Starting MedAnnotator Backend..."
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and add your API keys:"
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the backend
echo "Starting backend on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Use uv if available, otherwise fall back to python
if command -v uv &> /dev/null; then
    echo "Using uv to run backend..."
    uv run python -m src.api.main
else
    echo "Using python to run backend..."
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
        echo "WARNING: No virtual environment detected."
        echo "Consider installing uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo ""
    fi
    python -m src.api.main
fi
