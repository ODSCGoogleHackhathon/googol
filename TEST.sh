#!/bin/bash
# Smoke test script for MedAnnotator
# Tests core functionality without requiring API keys (uses mock data)

set -e  # Exit on error

echo "================================"
echo "MedAnnotator Smoke Test Suite"
echo "================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Detect Python command (uv run python, python3, or python)
if command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ ERROR: No Python found (tried: uv, python3, python)"
    exit 1
fi

# Test 1: Python version check
echo "Test 1: Checking Python version..."
python_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [ "$major_version" -ge 3 ] 2>/dev/null && [ "$minor_version" -ge 11 ] 2>/dev/null; then
    print_result 0 "Python version $python_version is compatible (requires 3.11+, using: $PYTHON_CMD)"
else
    print_result 1 "Python version $python_version is too old (requires 3.11+)"
fi
echo ""

# Test 2: Check required directories exist
echo "Test 2: Checking project structure..."
for dir in src src/api src/agent src/tools src/ui data; do
    if [ -d "$dir" ]; then
        print_result 0 "Directory exists: $dir"
    else
        print_result 1 "Directory missing: $dir"
    fi
done
echo ""

# Test 3: Check required files exist
echo "Test 3: Checking required files..."
for file in pyproject.toml .env.example .gitignore; do
    if [ -f "$file" ]; then
        print_result 0 "File exists: $file"
    else
        print_result 1 "File missing: $file"
    fi
done
echo ""

# Test 4: Check Python modules can be imported
echo "Test 4: Testing Python imports..."

test_import() {
    if $PYTHON_CMD -c "import $1" 2>/dev/null; then
        print_result 0 "Can import: $1"
    else
        print_result 1 "Cannot import: $1"
    fi
}

test_import "fastapi"
test_import "streamlit"
test_import "pydantic"
test_import "google.generativeai"
echo ""

# Test 5: Check src modules can be imported
echo "Test 5: Testing src module imports..."

test_src_import() {
    if $PYTHON_CMD -c "from $1 import $2" 2>/dev/null; then
        print_result 0 "Can import: $1.$2"
    else
        print_result 1 "Cannot import: $1.$2"
    fi
}

test_src_import "src.config" "settings"
test_src_import "src.schemas" "AnnotationOutput"
# test_src_import "src.tools.medgemma_tool" "MedGemmaTool"
echo ""

# Test 6: Test MedGemma tool import (skip initialization to avoid loading model)
# echo "Test 6: Testing MedGemma tool import..."
# if $PYTHON_CMD -c "from src.tools.medgemma_tool import MedGemmaTool" 2>/dev/null; then
#     print_result 0 "MedGemma tool imports successfully (skipping model load)"
# else
#     print_result 1 "MedGemma tool import failed"
# fi
# echo ""

# Test 7: Test configuration loading
echo "Test 7: Testing configuration..."
$PYTHON_CMD << 'EOF'
import sys
try:
    from src.config import settings

    # Check that config loads without errors
    assert hasattr(settings, 'gemini_model')
    assert hasattr(settings, 'backend_port')
    assert hasattr(settings, 'log_level')

    print(f"SUCCESS: Configuration loaded (model: {settings.gemini_model})")
    sys.exit(0)
except Exception as e:
    print(f"FAIL: Configuration test failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    print_result 0 "Configuration loads correctly"
else
    print_result 1 "Configuration failed to load"
fi
echo ""

# Test 8: Test Pydantic schemas
echo "Test 8: Testing Pydantic schemas..."
$PYTHON_CMD << 'EOF'
import sys
try:
    from src.schemas import Finding, AnnotationOutput

    # Test creating a Finding
    finding = Finding(
        label="Test Finding",
        location="Test Location",
        severity="Mild"
    )

    # Test creating an AnnotationOutput
    annotation = AnnotationOutput(
        patient_id="TEST-001",
        findings=[finding],
        confidence_score=0.85,
        generated_by="Test"
    )

    # Validate JSON serialization
    json_data = annotation.model_dump()

    print("SUCCESS: Pydantic schemas work correctly")
    sys.exit(0)
except Exception as e:
    print(f"FAIL: Schema test failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    print_result 0 "Pydantic schemas work"
else
    print_result 1 "Pydantic schemas failed"
fi
echo ""

# Test 9: Check documentation files
echo "Test 9: Checking documentation..."
for doc in ARCHITECTURE.md EXPLANATION.md DEMO.md README.md; do
    if [ -f "$doc" ]; then
        word_count=$(wc -w < "$doc")
        if [ "$word_count" -gt 100 ]; then
            print_result 0 "$doc exists and has content ($word_count words)"
        else
            print_result 1 "$doc exists but seems incomplete ($word_count words)"
        fi
    else
        print_result 1 "$doc is missing"
    fi
done
echo ""

# Test 10: FastAPI app can be imported (doesn't start server)
echo "Test 10: Testing FastAPI app import..."
$PYTHON_CMD << 'EOF'
import sys
try:
    from src.api.main import app

    # Check that routes are registered
    routes = [route.path for route in app.routes]

    if "/" in routes and "/health" in routes and "/annotate" in routes:
        print(f"SUCCESS: FastAPI app has all required routes: {routes}")
        sys.exit(0)
    else:
        print(f"FAIL: Missing routes. Found: {routes}")
        sys.exit(1)
except ModuleNotFoundError as e:
    if "torch" in str(e) or "transformers" in str(e):
        print(f"SKIP: FastAPI app import skipped (ML dependencies not installed: {e})")
        sys.exit(0)  # Exit with success for CI environments without ML stack
    else:
        print(f"FAIL: FastAPI import failed: {e}")
        sys.exit(1)
except Exception as e:
    print(f"FAIL: FastAPI import failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    print_result 0 "FastAPI app structure is correct (or ML deps skipped)"
else
    print_result 1 "FastAPI app structure has issues"
fi
echo ""

# Print summary
echo "================================"
echo "Test Summary"
echo "================================"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo "MedAnnotator is ready to run."
    echo ""
    echo "Next steps:"
    echo "1. Set up your .env file with GOOGLE_API_KEY"
    echo "2. Run backend: ./run_backend.sh"
    echo "3. Run frontend: ./run_frontend.sh"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo "Please fix the issues above before running the application."
    exit 1
fi
