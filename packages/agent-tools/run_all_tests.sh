#!/bin/bash
#
# Complete Test Suite for agent-tools
# Runs all unit tests, integration tests, and edge case tests
#

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║          Agent Tools - Complete Test Suite                  ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# Test counts
echo "📊 Test Categories:"
echo "  - Unit Tests (SessionSandbox): 6 tests"
echo "  - Unit Tests (Level 1 Tools): 12 tests"
echo "  - Integration Tests: 6 tests"
echo "  - Edge Case Tests: 21 tests"
echo "  - Concurrent Tests: 8 tests"
echo "  - Agent Integration Tests: 11 tests"
echo "  ────────────────────────────"
echo "  Total: 64 tests"
echo ""

# Run tests
echo "🧪 Running all tests..."
echo ""

python -m pytest tests/ -v --tb=short

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Test Summary                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Run with coverage
echo "📈 Generating coverage report..."
echo ""

python -m pytest tests/ \
    --cov=src/agent_tools \
    --cov-report=term \
    --cov-report=html \
    -q

echo ""
echo "✅ All tests completed!"
echo ""
echo "Coverage report: htmlcov/index.html"
echo ""
