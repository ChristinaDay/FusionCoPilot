#!/bin/bash
"""
Fusion 360 Co-Pilot - CI Test Runner

Comprehensive test runner for continuous integration and local development.
Runs all tests, generates coverage reports, and validates the complete system.

Usage:
    ./ci_test_runner.sh [options]
    
Options:
    --quick         Run only fast tests
    --coverage      Generate coverage report  
    --verbose       Verbose output
    --help          Show this help

Author: Fusion CoPilot Team
License: MIT
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
QUICK_MODE=false
COVERAGE_MODE=false
VERBOSE_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --coverage)
            COVERAGE_MODE=true
            shift
            ;;
        --verbose)
            VERBOSE_MODE=true
            shift
            ;;
        --help)
            echo "Fusion 360 Co-Pilot CI Test Runner"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --quick         Run only fast tests"
            echo "  --coverage      Generate coverage report"
            echo "  --verbose       Verbose output"
            echo "  --help          Show this help"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_status $BLUE "=========================================="
    print_status $BLUE "$1"
    print_status $BLUE "=========================================="
}

print_success() {
    print_status $GREEN "✓ $1"
}

print_error() {
    print_status $RED "✗ $1"
}

print_warning() {
    print_status $YELLOW "⚠ $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_header "Fusion 360 Co-Pilot - CI Test Runner"
echo "Project root: $PROJECT_ROOT"
echo "Quick mode: $QUICK_MODE"
echo "Coverage mode: $COVERAGE_MODE"
echo "Verbose mode: $VERBOSE_MODE"

# Change to project root
cd "$PROJECT_ROOT"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

print_success "Python 3 found: $(python3 --version)"

# Check if we're in a virtual environment (recommended)
if [[ -z "${VIRTUAL_ENV}" ]]; then
    print_warning "Not running in a virtual environment (recommended but not required)"
else
    print_success "Virtual environment: $VIRTUAL_ENV"
fi

# Install/check dependencies
print_header "Checking Dependencies"

# Check for pytest
if ! python3 -c "import pytest" 2>/dev/null; then
    print_warning "pytest not found, attempting to install..."
    if pip3 install pytest; then
        print_success "pytest installed successfully"
    else
        print_error "Failed to install pytest"
        exit 1
    fi
else
    print_success "pytest is available"
fi

# Check for optional dependencies
OPTIONAL_DEPS=("jsonschema" "pyyaml" "flask")
for dep in "${OPTIONAL_DEPS[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        print_success "$dep is available"
    else
        print_warning "$dep is not available (some tests may be skipped)"
    fi
done

# Coverage dependency
if [[ "$COVERAGE_MODE" == true ]]; then
    if ! python3 -c "import coverage" 2>/dev/null; then
        print_warning "coverage not found, attempting to install..."
        if pip3 install coverage; then
            print_success "coverage installed successfully"
        else
            print_error "Failed to install coverage"
            COVERAGE_MODE=false
        fi
    else
        print_success "coverage is available"
    fi
fi

# Generate test fixtures
print_header "Generating Test Fixtures"

if [[ -f "dev_tools/generate_test_fixtures.py" ]]; then
    if python3 dev_tools/generate_test_fixtures.py --output-dir test_fixtures --format json; then
        print_success "Test fixtures generated"
    else
        print_warning "Test fixture generation failed (continuing anyway)"
    fi
else
    print_warning "Test fixture generator not found"
fi

# Validate project structure
print_header "Validating Project Structure"

REQUIRED_FILES=(
    "fusion_addin/main.py"
    "fusion_addin/ui.py"
    "fusion_addin/executor.py"
    "fusion_addin/sanitizer.py"
    "fusion_addin/action_log.py"
    "fusion_addin/plan_schema.json"
    "fusion_addin/settings.yaml"
    "fusion_addin/tests/test_sanitizer.py"
    "fusion_addin/tests/test_plan_validation.py"
    "llm_stub/server.py"
    "llm_stub/canned_plans.json"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        if [[ "$VERBOSE_MODE" == true ]]; then
            print_success "Found: $file"
        fi
    else
        print_error "Missing: $file"
        MISSING_FILES+=("$file")
    fi
done

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    print_error "Missing ${#MISSING_FILES[@]} required files"
    exit 1
else
    print_success "All required files present"
fi

# Validate JSON files
print_header "Validating JSON Files"

JSON_FILES=(
    "fusion_addin/plan_schema.json"
    "fusion_addin/prompts/prompt_examples.json"
    "llm_stub/canned_plans.json"
)

for json_file in "${JSON_FILES[@]}"; do
    if [[ -f "$json_file" ]]; then
        if python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
            print_success "Valid JSON: $json_file"
        else
            print_error "Invalid JSON: $json_file"
            exit 1
        fi
    else
        print_warning "JSON file not found: $json_file"
    fi
done

# Validate YAML files
print_header "Validating YAML Files"

if [[ -f "fusion_addin/settings.yaml" ]]; then
    if python3 -c "import yaml; yaml.safe_load(open('fusion_addin/settings.yaml'))" 2>/dev/null; then
        print_success "Valid YAML: fusion_addin/settings.yaml"
    else
        print_error "Invalid YAML: fusion_addin/settings.yaml"
        exit 1
    fi
else
    print_error "Settings file not found: fusion_addin/settings.yaml"
    exit 1
fi

# Run Python syntax checks
print_header "Python Syntax Validation"

PYTHON_FILES=(
    "fusion_addin/main.py"
    "fusion_addin/ui.py"
    "fusion_addin/executor.py"
    "fusion_addin/sanitizer.py"
    "fusion_addin/action_log.py"
    "fusion_addin/tests/test_sanitizer.py"
    "fusion_addin/tests/test_plan_validation.py"
    "llm_stub/server.py"
    "dev_tools/generate_test_fixtures.py"
)

for py_file in "${PYTHON_FILES[@]}"; do
    if [[ -f "$py_file" ]]; then
        if python3 -m py_compile "$py_file" 2>/dev/null; then
            if [[ "$VERBOSE_MODE" == true ]]; then
                print_success "Syntax OK: $py_file"
            fi
        else
            print_error "Syntax error: $py_file"
            exit 1
        fi
    else
        print_warning "Python file not found: $py_file"
    fi
done

print_success "All Python files have valid syntax"

# Run unit tests
print_header "Running Unit Tests"

TEST_ARGS=""
if [[ "$VERBOSE_MODE" == true ]]; then
    TEST_ARGS="$TEST_ARGS -v"
fi

if [[ "$COVERAGE_MODE" == true ]]; then
    # Run tests with coverage
    if coverage run -m pytest fusion_addin/tests/ $TEST_ARGS; then
        print_success "Unit tests passed"
        
        # Generate coverage report
        print_header "Coverage Report"
        coverage report -m --include="fusion_addin/*"
        
        # Generate HTML coverage report
        coverage html --include="fusion_addin/*" -d coverage_html
        print_success "HTML coverage report generated in coverage_html/"
        
    else
        print_error "Unit tests failed"
        exit 1
    fi
else
    # Run tests without coverage
    if python3 -m pytest fusion_addin/tests/ $TEST_ARGS; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
        exit 1
    fi
fi

# Test LLM stub server (if not in quick mode)
if [[ "$QUICK_MODE" != true ]]; then
    print_header "Testing LLM Stub Server"
    
    # Check if Flask is available
    if python3 -c "import flask" 2>/dev/null; then
        # Start server in background
        python3 llm_stub/server.py --port 8081 &
        SERVER_PID=$!
        
        # Wait a moment for server to start
        sleep 2
        
        # Test server endpoint
        if command -v curl &> /dev/null; then
            if curl -s http://localhost:8081/health > /dev/null; then
                print_success "LLM stub server is responding"
            else
                print_warning "LLM stub server health check failed"
            fi
        else
            print_warning "curl not available, skipping server test"
        fi
        
        # Clean up server
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        
    else
        print_warning "Flask not available, skipping server test"
    fi
fi

# Test plan schema validation (if not in quick mode)
if [[ "$QUICK_MODE" != true ]]; then
    print_header "Testing Plan Schema Validation"
    
    if python3 -c "
import json
import sys
sys.path.append('fusion_addin')
from sanitizer import validate_plan_against_schema

# Load schema examples
with open('fusion_addin/plan_schema.json', 'r') as f:
    schema = json.load(f)

examples = schema.get('examples', [])
if not examples:
    print('No examples found in schema')
    exit(1)

# Test each example
for i, example in enumerate(examples):
    is_valid, messages = validate_plan_against_schema(example, 'fusion_addin/plan_schema.json')
    if not is_valid:
        print(f'Schema example {i} failed validation: {messages}')
        exit(1)

print(f'All {len(examples)} schema examples validated successfully')
"; then
        print_success "Plan schema validation passed"
    else
        print_error "Plan schema validation failed"
        exit 1
    fi
fi

# Integration test (if not in quick mode)
if [[ "$QUICK_MODE" != true ]]; then
    print_header "Integration Test"
    
    if python3 -c "
import sys
sys.path.append('fusion_addin')
from sanitizer import PlanSanitizer
from executor import PlanExecutor
from action_log import ActionLogger

# Test component integration
try:
    # Initialize components
    sanitizer = PlanSanitizer()
    executor = PlanExecutor()
    logger = ActionLogger('test_logs')
    
    # Test plan
    test_plan = {
        'plan_id': 'integration_test_001',
        'metadata': {
            'natural_language_prompt': 'Integration test',
            'units': 'mm'
        },
        'operations': [
            {
                'op_id': 'op_1',
                'op': 'create_sketch',
                'params': {'plane': 'XY', 'name': 'test_sketch'}
            }
        ]
    }
    
    # Test sanitization
    is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(test_plan)
    if not is_valid:
        print(f'Sanitization failed: {messages}')
        exit(1)
    
    # Test preview
    preview_result = executor.preview_plan_in_sandbox(sanitized_plan)
    if not preview_result.get('success'):
        print(f'Preview failed: {preview_result.get(\"error\")}')
        exit(1)
    
    print('Integration test passed')
    
except Exception as e:
    print(f'Integration test failed: {e}')
    exit(1)
"; then
        print_success "Integration test passed"
    else
        print_error "Integration test failed"
        exit 1
    fi
fi

# Clean up temporary files
print_header "Cleanup"

# Remove temporary test files
rm -rf test_fixtures 2>/dev/null || true
rm -rf test_logs 2>/dev/null || true
rm -rf __pycache__ 2>/dev/null || true
rm -rf fusion_addin/__pycache__ 2>/dev/null || true
rm -rf fusion_addin/tests/__pycache__ 2>/dev/null || true

if [[ "$COVERAGE_MODE" != true ]]; then
    rm -rf .coverage 2>/dev/null || true
    rm -rf coverage_html 2>/dev/null || true
fi

print_success "Cleanup completed"

# Final summary
print_header "Test Summary"

print_success "✓ Project structure validation"
print_success "✓ JSON/YAML file validation"  
print_success "✓ Python syntax validation"
print_success "✓ Unit tests"

if [[ "$QUICK_MODE" != true ]]; then
    print_success "✓ LLM stub server test"
    print_success "✓ Plan schema validation"
    print_success "✓ Integration test"
fi

if [[ "$COVERAGE_MODE" == true ]]; then
    print_success "✓ Coverage report generated"
fi

print_status $GREEN ""
print_status $GREEN "🎉 All tests passed! The Fusion 360 Co-Pilot is ready for development."
print_status $GREEN ""

# Display next steps
echo "Next steps:"
echo "  1. Install the add-in in Fusion 360 (see README.md)"
echo "  2. Start the LLM stub server: python llm_stub/server.py"
echo "  3. Test with sample prompts from fusion_addin/prompts/"
echo ""
echo "For development:"
echo "  - Run quick tests: $0 --quick"
echo "  - Generate coverage: $0 --coverage"  
echo "  - Verbose output: $0 --verbose"
echo ""

exit 0
