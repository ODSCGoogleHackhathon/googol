#!/bin/bash
# Installation script for MedAnnotator using uv

set -e  # Exit on error

echo "================================"
echo "MedAnnotator Installation"
echo "================================"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv not found. Installing uv...${NC}"

    # Install uv
    if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    else
        echo "Unsupported OS. Please install uv manually from https://github.com/astral-sh/uv"
        exit 1
    fi

    echo -e "${GREEN}✓ uv installed successfully${NC}"
else
    echo -e "${GREEN}✓ uv is already installed${NC}"
fi

echo ""
echo "Installing Python dependencies with uv..."
echo ""

# Sync dependencies
uv sync

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Set up your environment:"
echo "   cp .env.example .env"
echo "   # Edit .env and add your GOOGLE_API_KEY"
echo ""
echo "2. Activate the virtual environment:"
echo "   source .venv/bin/activate  # On macOS/Linux"
echo "   .venv\\Scripts\\activate     # On Windows"
echo ""
echo "3. Run the application:"
echo "   ./run_backend.sh  # In one terminal"
echo "   ./run_frontend.sh # In another terminal"
echo ""
echo "Or run with uv directly (no activation needed):"
echo "   uv run python -m src.api.main        # Backend"
echo "   uv run streamlit run src/ui/app.py   # Frontend"
echo ""
