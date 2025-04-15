#!/bin/bash
# FastJango PyPI Publishing Script
# This script helps with the process of publishing FastJango to PyPI

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}FastJango PyPI Publishing Tool${NC}"
echo "==============================="

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo -e "${YELLOW}Twine is not installed. Installing...${NC}"
    pip install twine
fi

# Check if build is installed
if ! command -v build &> /dev/null; then
    echo -e "${YELLOW}Build package is not installed. Installing...${NC}"
    pip install build
fi

# Clean up previous builds
clean() {
    echo -e "${BLUE}Cleaning previous builds...${NC}"
    rm -rf build/ dist/ *.egg-info/
}

# Build the package
build_package() {
    echo -e "${BLUE}Building FastJango package...${NC}"
    python -m build
}

# Check the package
check_package() {
    echo -e "${BLUE}Checking package...${NC}"
    twine check dist/*
}

# Upload to TestPyPI
upload_test() {
    echo -e "${YELLOW}Uploading to TestPyPI...${NC}"
    twine upload --repository testpypi dist/*
    echo -e "${GREEN}Package uploaded to TestPyPI!${NC}"
    echo -e "Install with: ${YELLOW}pip install --index-url https://test.pypi.org/simple/ fastjango${NC}"
}

# Upload to PyPI
upload_prod() {
    echo -e "${YELLOW}Uploading to PyPI...${NC}"
    twine upload dist/*
    echo -e "${GREEN}Package uploaded to PyPI!${NC}"
    echo -e "Install with: ${YELLOW}pip install fastjango${NC}"
}

# Install locally for testing
install_local() {
    echo -e "${BLUE}Installing locally for testing...${NC}"
    pip install -e .
    echo -e "${GREEN}Package installed locally!${NC}"
}

# Run all tests
run_tests() {
    echo -e "${BLUE}Running FastJango tests...${NC}"
    
    # Check if tests.sh exists and is executable
    if [ -f "./tests.sh" ]; then
        if [ ! -x "./tests.sh" ]; then
            chmod +x ./tests.sh
        fi
        
        # Run the test script
        ./tests.sh
        
        # Check if tests passed
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}All tests passed!${NC}"
            return 0
        else
            echo -e "${RED}Tests failed! Please fix errors before proceeding.${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Warning: tests.sh script not found. Skipping tests.${NC}"
        echo -e "${YELLOW}To run tests, create a tests.sh script in the root directory.${NC}"
    fi
}

# Update version
update_version() {
    if [ -z "$1" ]; then
        echo -e "${RED}No version specified. Use: ./publish.sh version x.y.z${NC}"
        exit 1
    fi
    
    VERSION=$1
    echo -e "${BLUE}Updating version to $VERSION...${NC}"
    
    # Update pyproject.toml
    sed -i.bak "s/version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$VERSION\"/" pyproject.toml
    rm -f pyproject.toml.bak
    
    echo -e "${GREEN}Version updated to $VERSION!${NC}"
}

# Display help message
show_help() {
    echo "Usage: ./publish.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  clean       Clean previous builds"
    echo "  build       Build the package"
    echo "  check       Check the package for errors"
    echo "  test        Upload to TestPyPI"
    echo "  publish     Upload to PyPI"
    echo "  install     Install locally for testing"
    echo "  run-tests   Run the test suite"
    echo "  version     Update version number (requires additional argument, e.g., version 0.1.1)"
    echo "  all-test    Clean, run tests, build, check, and upload to TestPyPI"
    echo "  all         Clean, run tests, build, check, and upload to PyPI"
    echo "  help        Show this help message"
}

# Process commands
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# Process each argument
for arg in "$@"; do
    case $arg in
        clean)
            clean
            ;;
        build)
            build_package
            ;;
        check)
            check_package
            ;;
        test)
            upload_test
            ;;
        publish)
            upload_prod
            ;;
        install)
            install_local
            ;;
        run-tests)
            run_tests
            ;;
        version)
            shift
            update_version "$1"
            shift
            ;;
        all-test)
            clean
            run_tests
            build_package
            check_package
            upload_test
            ;;
        all)
            clean
            run_tests
            build_package
            check_package
            upload_prod
            ;;
        help)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Done!${NC}" 