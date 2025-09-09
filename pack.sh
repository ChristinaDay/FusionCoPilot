#!/bin/bash
"""
Fusion 360 Co-Pilot - Development Pack Builder

Creates the complete fusion-copilot-devpack.zip file with all components
ready for distribution and installation.

Usage:
    ./pack.sh [options]
    
Options:
    --output DIR        Output directory (default: current directory)
    --name NAME         Archive name (default: fusion-copilot-devpack)
    --include-tests     Include test files in the pack
    --verbose           Verbose output
    --clean             Clean temporary files after packing
    --help              Show this help

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
OUTPUT_DIR="."
ARCHIVE_NAME="fusion-copilot-devpack"
INCLUDE_TESTS=false
VERBOSE=false
CLEAN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --name)
            ARCHIVE_NAME="$2"
            shift 2
            ;;
        --include-tests)
            INCLUDE_TESTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --help)
            echo "Fusion 360 Co-Pilot Development Pack Builder"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --output DIR        Output directory (default: current directory)"
            echo "  --name NAME         Archive name (default: fusion-copilot-devpack)"
            echo "  --include-tests     Include test files in the pack"
            echo "  --verbose           Verbose output"
            echo "  --clean             Clean temporary files after packing"
            echo "  --help              Show this help"
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
PROJECT_ROOT="$SCRIPT_DIR"

print_header "Fusion 360 Co-Pilot - Development Pack Builder"
echo "Project root: $PROJECT_ROOT"
echo "Output directory: $OUTPUT_DIR"
echo "Archive name: $ARCHIVE_NAME"
echo "Include tests: $INCLUDE_TESTS"

# Change to project root
cd "$PROJECT_ROOT"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Create temporary directory for packing
TEMP_DIR=$(mktemp -d)
PACK_DIR="$TEMP_DIR/$ARCHIVE_NAME"

if [[ "$VERBOSE" == true ]]; then
    print_status $BLUE "Temporary directory: $TEMP_DIR"
fi

# Create pack directory structure
mkdir -p "$PACK_DIR"

print_header "Copying Files"

# Function to copy file with status
copy_file() {
    local src="$1"
    local dst="$2"
    
    if [[ -f "$src" ]]; then
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        if [[ "$VERBOSE" == true ]]; then
            print_success "Copied: $src"
        fi
        return 0
    else
        print_error "Missing: $src"
        return 1
    fi
}

# Function to copy directory with status
copy_dir() {
    local src="$1"
    local dst="$2"
    
    if [[ -d "$src" ]]; then
        mkdir -p "$(dirname "$dst")"
        cp -r "$src" "$dst"
        if [[ "$VERBOSE" == true ]]; then
            print_success "Copied directory: $src"
        fi
        return 0
    else
        print_error "Missing directory: $src"
        return 1
    fi
}

# Copy root files
MISSING_FILES=()

copy_file "README.md" "$PACK_DIR/README.md" || MISSING_FILES+=("README.md")
copy_file "LICENSE" "$PACK_DIR/LICENSE" || MISSING_FILES+=("LICENSE")
copy_file "CHANGELOG.md" "$PACK_DIR/CHANGELOG.md" || MISSING_FILES+=("CHANGELOG.md")
copy_file "sample_prompts_and_expected_plans.md" "$PACK_DIR/sample_prompts_and_expected_plans.md" || MISSING_FILES+=("sample_prompts_and_expected_plans.md")

# Copy fusion_addin directory
if [[ -d "fusion_addin" ]]; then
    # Core add-in files
    copy_file "fusion_addin/manifest.json" "$PACK_DIR/fusion_addin/manifest.json" || MISSING_FILES+=("fusion_addin/manifest.json")
    copy_file "fusion_addin/README_ADDIN.md" "$PACK_DIR/fusion_addin/README_ADDIN.md" || MISSING_FILES+=("fusion_addin/README_ADDIN.md")
    copy_file "fusion_addin/icon.png" "$PACK_DIR/fusion_addin/icon.png" || MISSING_FILES+=("fusion_addin/icon.png")
    copy_file "fusion_addin/main.py" "$PACK_DIR/fusion_addin/main.py" || MISSING_FILES+=("fusion_addin/main.py")
    copy_file "fusion_addin/ui.py" "$PACK_DIR/fusion_addin/ui.py" || MISSING_FILES+=("fusion_addin/ui.py")
    copy_file "fusion_addin/executor.py" "$PACK_DIR/fusion_addin/executor.py" || MISSING_FILES+=("fusion_addin/executor.py")
    copy_file "fusion_addin/sanitizer.py" "$PACK_DIR/fusion_addin/sanitizer.py" || MISSING_FILES+=("fusion_addin/sanitizer.py")
    copy_file "fusion_addin/action_log.py" "$PACK_DIR/fusion_addin/action_log.py" || MISSING_FILES+=("fusion_addin/action_log.py")
    copy_file "fusion_addin/plan_schema.json" "$PACK_DIR/fusion_addin/plan_schema.json" || MISSING_FILES+=("fusion_addin/plan_schema.json")
    copy_file "fusion_addin/settings.yaml" "$PACK_DIR/fusion_addin/settings.yaml" || MISSING_FILES+=("fusion_addin/settings.yaml")
    
    # Prompts directory
    copy_dir "fusion_addin/prompts" "$PACK_DIR/fusion_addin/prompts" || MISSING_FILES+=("fusion_addin/prompts/")
    
    # Tests directory (optional)
    if [[ "$INCLUDE_TESTS" == true ]]; then
        copy_dir "fusion_addin/tests" "$PACK_DIR/fusion_addin/tests" || print_warning "Tests directory not found"
    fi
    
    print_success "Fusion add-in files copied"
else
    print_error "fusion_addin directory not found"
    MISSING_FILES+=("fusion_addin/")
fi

# Copy llm_stub directory
copy_dir "llm_stub" "$PACK_DIR/llm_stub" || MISSING_FILES+=("llm_stub/")

# Copy dev_tools directory
copy_dir "dev_tools" "$PACK_DIR/dev_tools" || MISSING_FILES+=("dev_tools/")

# Copy ui_mock directory
copy_dir "ui_mock" "$PACK_DIR/ui_mock" || MISSING_FILES+=("ui_mock/")

# Create logs directory structure
mkdir -p "$PACK_DIR/fusion_addin/logs/actions"

# Check for missing files
if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    print_error "Missing ${#MISSING_FILES[@]} files/directories:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    echo ""
    echo "Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_error "Aborting due to missing files"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
else
    print_success "All required files present"
fi

# Generate requirements.txt for Python dependencies
print_header "Generating Requirements"

cat > "$PACK_DIR/requirements.txt" << EOF
# Fusion 360 Co-Pilot Dependencies
# 
# Core dependencies for development and testing
pytest>=7.0.0
jsonschema>=4.0.0
PyYAML>=6.0

# Optional dependencies for LLM stub server
flask>=2.0.0
flask-cors>=4.0.0

# Optional dependencies for enhanced functionality
requests>=2.28.0

# Development dependencies
coverage>=6.0.0

# Note: Fusion 360 provides its own Python environment with many packages pre-installed.
# These requirements are primarily for development, testing, and the LLM stub server.
EOF

print_success "Generated requirements.txt"

# Generate installation script
print_header "Generating Installation Scripts"

# Windows batch file
cat > "$PACK_DIR/install.bat" << 'EOF'
@echo off
echo Fusion 360 Co-Pilot Installation
echo ================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10+ and try again
    pause
    exit /b 1
)

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Open Fusion 360
echo 2. Go to Tools ^> Scripts and Add-Ins
echo 3. Click Add-Ins tab, then + button
echo 4. Select the fusion_addin folder
echo 5. Click Run to start the Co-Pilot
echo.
echo For local development, start the LLM stub server:
echo   python llm_stub\server.py
echo.
pause
EOF

# Unix shell script
cat > "$PACK_DIR/install.sh" << 'EOF'
#!/bin/bash
echo "Fusion 360 Co-Pilot Installation"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.10+ and try again"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Install dependencies
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    echo "Warning: pip not found, you may need to install dependencies manually"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Open Fusion 360"
echo "2. Go to Tools > Scripts and Add-Ins"
echo "3. Click Add-Ins tab, then + button"
echo "4. Select the fusion_addin folder"
echo "5. Click Run to start the Co-Pilot"
echo ""
echo "For local development, start the LLM stub server:"
echo "  python3 llm_stub/server.py"
echo ""
EOF

chmod +x "$PACK_DIR/install.sh"

print_success "Generated installation scripts"

# Validate pack structure
print_header "Validating Pack Structure"

EXPECTED_STRUCTURE=(
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    "requirements.txt"
    "install.sh"
    "install.bat"
    "fusion_addin/manifest.json"
    "fusion_addin/main.py"
    "fusion_addin/ui.py"
    "fusion_addin/executor.py"
    "fusion_addin/sanitizer.py"
    "fusion_addin/action_log.py"
    "fusion_addin/plan_schema.json"
    "fusion_addin/settings.yaml"
    "fusion_addin/prompts/prompt_examples.json"
    "llm_stub/server.py"
    "llm_stub/canned_plans.json"
    "dev_tools/generate_test_fixtures.py"
    "dev_tools/ci_test_runner.sh"
    "ui_mock/action_log_mock.html"
    "ui_mock/action_log_spec.md"
)

VALIDATION_ERRORS=()

for file in "${EXPECTED_STRUCTURE[@]}"; do
    if [[ -f "$PACK_DIR/$file" ]]; then
        if [[ "$VERBOSE" == true ]]; then
            print_success "Found: $file"
        fi
    else
        print_error "Missing in pack: $file"
        VALIDATION_ERRORS+=("$file")
    fi
done

if [[ ${#VALIDATION_ERRORS[@]} -gt 0 ]]; then
    print_error "Pack validation failed: ${#VALIDATION_ERRORS[@]} missing files"
    if [[ "$VERBOSE" != true ]]; then
        echo "Run with --verbose to see all missing files"
    fi
else
    print_success "Pack structure validation passed"
fi

# Calculate pack size
PACK_SIZE=$(du -sh "$PACK_DIR" | cut -f1)
FILE_COUNT=$(find "$PACK_DIR" -type f | wc -l)

print_success "Pack contains $FILE_COUNT files ($PACK_SIZE total)"

# Create the zip archive
print_header "Creating Archive"

ARCHIVE_PATH="$OUTPUT_DIR/$ARCHIVE_NAME.zip"

# Remove existing archive if present
if [[ -f "$ARCHIVE_PATH" ]]; then
    rm "$ARCHIVE_PATH"
    print_warning "Removed existing archive: $ARCHIVE_PATH"
fi

# Create zip archive
cd "$TEMP_DIR"
if zip -r "$ARCHIVE_PATH" "$ARCHIVE_NAME" > /dev/null 2>&1; then
    print_success "Created archive: $ARCHIVE_PATH"
else
    print_error "Failed to create archive"
    cd "$PROJECT_ROOT"
    rm -rf "$TEMP_DIR"
    exit 1
fi

cd "$PROJECT_ROOT"

# Get final archive info
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_PATH" | cut -f1)
print_success "Archive size: $ARCHIVE_SIZE"

# Generate checksum
if command -v sha256sum &> /dev/null; then
    CHECKSUM=$(sha256sum "$ARCHIVE_PATH" | cut -d' ' -f1)
    print_success "SHA256: $CHECKSUM"
elif command -v shasum &> /dev/null; then
    CHECKSUM=$(shasum -a 256 "$ARCHIVE_PATH" | cut -d' ' -f1)
    print_success "SHA256: $CHECKSUM"
fi

# Clean up temporary directory
if [[ "$CLEAN" == true ]]; then
    rm -rf "$TEMP_DIR"
    print_success "Cleaned temporary files"
else
    print_warning "Temporary files left in: $TEMP_DIR"
fi

# Final summary
print_header "Pack Generation Complete"

print_success "✓ Archive created: $ARCHIVE_PATH"
print_success "✓ Size: $ARCHIVE_SIZE ($FILE_COUNT files)"
if [[ -n "$CHECKSUM" ]]; then
    print_success "✓ Checksum: $CHECKSUM"
fi

echo ""
echo "Installation instructions:"
echo "1. Extract $ARCHIVE_NAME.zip"
echo "2. Run install.sh (Unix/Mac) or install.bat (Windows)"
echo "3. Follow the on-screen instructions"
echo ""
echo "For development:"
echo "1. Start LLM stub: python llm_stub/server.py"
echo "2. Run tests: ./dev_tools/ci_test_runner.sh"
echo "3. View UI mockup: ui_mock/action_log_mock.html"
echo ""

print_status $GREEN "🎉 Fusion 360 Co-Pilot development pack is ready!"

exit 0
