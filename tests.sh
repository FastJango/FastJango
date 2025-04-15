#!/bin/bash
# FastJango Test Suite
# Tests the functionality of fastjango-admin and manage.py

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TEMP_DIR="_test_fastjango"

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED: $2${NC}"
    else
        echo -e "${RED}✗ FAILED: $2${NC}"
        exit 1
    fi
}

echo -e "${BLUE}Running FastJango Test Suite${NC}"
echo "==============================="

# Setup
echo -e "${BLUE}Setting up test environment...${NC}"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Check project structure
echo -e "${BLUE}Test 1: Checking project structure${NC}"

# Check fastjango-admin
if [ ! -f "./fastjango-admin.py" ]; then
    echo -e "${RED}fastjango-admin.py not found${NC}"
    exit 1
fi
print_status 0 "fastjango-admin.py exists"

# Check core modules
if [ ! -d "./fastjango" ]; then
    echo -e "${RED}fastjango package not found${NC}"
    exit 1
fi
print_status 0 "fastjango package exists"

if [ ! -d "./fastjango/core" ]; then
    echo -e "${RED}core module not found${NC}"
    exit 1
fi
print_status 0 "core module exists"

if [ ! -f "./fastjango/core/asgi.py" ]; then
    echo -e "${RED}asgi.py not found${NC}"
    exit 1
fi
print_status 0 "asgi.py exists"

# Check CLI modules
if [ ! -d "./fastjango/cli" ]; then
    echo -e "${RED}cli module not found${NC}"
    exit 1
fi
print_status 0 "cli module exists"

if [ ! -d "./fastjango/cli/commands" ]; then
    echo -e "${RED}commands module not found${NC}"
    exit 1
fi
print_status 0 "commands module exists"

# Check templates
if [ ! -d "./fastjango/templates" ]; then
    echo -e "${RED}templates not found${NC}"
    exit 1
fi
print_status 0 "templates directory exists"

if [ ! -d "./fastjango/templates/project_template" ]; then
    echo -e "${RED}project_template not found${NC}"
    exit 1
fi
print_status 0 "project template exists"

# Check project template files
PROJECT_TPL="./fastjango/templates/project_template/{{project_name}}"

if [ ! -f "$PROJECT_TPL/urls.py" ]; then
    echo -e "${RED}project urls.py template not found${NC}"
    exit 1
fi
print_status 0 "project urls.py template exists"

if [ ! -f "$PROJECT_TPL/settings.py" ]; then
    echo -e "${RED}project settings.py template not found${NC}"
    exit 1
fi
print_status 0 "project settings.py template exists"

if [ ! -f "$PROJECT_TPL/asgi.py" ]; then
    echo -e "${RED}project asgi.py template not found${NC}"
    exit 1
fi
print_status 0 "project asgi.py template exists"

# Check app template
if [ ! -d "./fastjango/templates/app_template" ]; then
    echo -e "${RED}app_template not found${NC}"
    exit 1
fi
print_status 0 "app template exists"

# Check key files
if [ ! -f "./fastjango/http.py" ]; then
    echo -e "${RED}http.py not found${NC}"
    exit 1
fi
print_status 0 "http.py exists"

if [ ! -f "./fastjango/urls.py" ]; then
    echo -e "${RED}urls.py not found${NC}"
    exit 1
fi
print_status 0 "urls.py exists"

# Check DEBUG and STATIC_URL in settings template
echo -e "${BLUE}Test 2: Checking settings template${NC}"

if ! grep "DEBUG = True" "$PROJECT_TPL/settings.py" >/dev/null 2>&1; then
    echo -e "${RED}DEBUG = True not found in settings template${NC}"
    exit 1
fi
print_status 0 "DEBUG is set to True by default"

if ! grep "STATIC_URL" "$PROJECT_TPL/settings.py" >/dev/null 2>&1; then
    echo -e "${RED}STATIC_URL not found in settings template${NC}"
    exit 1
fi
print_status 0 "STATIC_URL is configured in template"

# Check package configuration
echo -e "${BLUE}Test 3: Checking package configuration${NC}"

if [ ! -f "./pyproject.toml" ]; then
    echo -e "${RED}pyproject.toml not found${NC}"
    exit 1
fi
print_status 0 "pyproject.toml exists"

# Cleanup
echo -e "${BLUE}Cleaning up...${NC}"
rm -rf $TEMP_DIR

echo -e "${GREEN}All tests passed successfully!${NC}" 