#!/bin/bash
# ============================================================================
# FutureFeed User-Org Service Test Runner
# ============================================================================
# This script runs all tests for the user-org service and generates a report.
#
# Usage:
#   ./run_tests.sh           # Run all tests
#   ./run_tests.sh --cov     # Run with coverage report
#   ./run_tests.sh --html    # Run with HTML coverage report
#
# Requirements:
#   pip install -r tests/requirements-test.txt
# ============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  FutureFeed User-Org Service Tests"
echo "============================================"
echo ""

# Check if running from correct directory
if [ ! -f "src/main.py" ]; then
    echo -e "${RED}Error: Please run from services/user-org directory${NC}"
    exit 1
fi

# Install test dependencies if needed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install -r tests/requirements-test.txt
fi

# Determine test command based on arguments
if [[ "$1" == "--cov" ]]; then
    echo -e "${YELLOW}Running tests with coverage...${NC}"
    python -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
elif [[ "$1" == "--html" ]]; then
    echo -e "${YELLOW}Running tests with HTML coverage report...${NC}"
    python -m pytest tests/ -v --tb=short --cov=src --cov-report=html
    echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
else
    echo -e "${YELLOW}Running all tests...${NC}"
    python -m pytest tests/ -v --tb=short
fi

# Capture exit code
EXIT_CODE=$?

echo ""
echo "============================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "  ${GREEN}✅ All tests passed!${NC}"
else
    echo -e "  ${RED}❌ Some tests failed!${NC}"
fi
echo "============================================"

exit $EXIT_CODE
