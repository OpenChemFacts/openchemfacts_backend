#!/bin/bash
# Pre-deployment validation script
# Runs checks before deploying to production
# Usage: ./scripts/pre_deploy_check.sh

set -e

echo "=========================================="
echo "  Pre-Deployment Validation Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any checks fail
FAILED_CHECKS=0

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print info
print_info() {
    echo -e "ℹ️  $1"
}

echo "1. Checking Git status..."
echo "----------------------------------------"
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Uncommitted changes detected:"
    git status --short
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Please commit or stash changes first."
        exit 1
    fi
else
    print_success "No uncommitted changes"
fi
echo ""

echo "2. Checking for sensitive data..."
echo "----------------------------------------"
SENSITIVE_PATTERNS=("password" "secret" "api_key" "token" "private_key")
FOUND_SENSITIVE=false

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if grep -r -i "$pattern" app/ --exclude-dir=__pycache__ 2>/dev/null | grep -v "#.*$pattern" | grep -v "def.*$pattern" | grep -v "import.*$pattern" > /dev/null; then
        print_warning "Potential sensitive data found (pattern: $pattern)"
        FOUND_SENSITIVE=true
    fi
done

if [ "$FOUND_SENSITIVE" = false ]; then
    print_success "No obvious sensitive data found"
fi
echo ""

echo "3. Checking Python syntax..."
echo "----------------------------------------"
SYNTAX_ERRORS=0
for file in app/*.py; do
    if [ -f "$file" ]; then
        if ! python -m py_compile "$file" 2>/dev/null; then
            print_error "Syntax error in $file"
            SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
        fi
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    print_success "All Python files have valid syntax"
else
    print_error "$SYNTAX_ERRORS file(s) with syntax errors"
fi
echo ""

echo "4. Checking required files..."
echo "----------------------------------------"
MISSING_FILES=0

if [ ! -f "Procfile" ]; then
    print_error "Procfile not found"
    MISSING_FILES=$((MISSING_FILES + 1))
else
    print_success "Procfile exists"
fi

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found"
    MISSING_FILES=$((MISSING_FILES + 1))
else
    print_success "requirements.txt exists"
fi

if [ ! -f "app/main.py" ]; then
    print_error "app/main.py not found"
    MISSING_FILES=$((MISSING_FILES + 1))
else
    print_success "app/main.py exists"
fi

# Check for data files (optional, may not be in Git)
if [ ! -f "data/results_ecotox_ssd.parquet" ] && [ ! -f "data/results_EF_benchmark.parquet" ]; then
    print_warning "No data files found in data/ directory"
else
    print_success "Data files found"
fi

if [ $MISSING_FILES -gt 0 ]; then
    print_error "$MISSING_FILES required file(s) missing"
fi
echo ""

echo "5. Checking Procfile content..."
echo "----------------------------------------"
if grep -q "uvicorn app.main:app" Procfile; then
    print_success "Procfile contains correct uvicorn command"
else
    print_error "Procfile may be incorrect"
    print_info "Expected: web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
fi
echo ""

echo "6. Checking .gitignore..."
echo "----------------------------------------"
if [ -f ".gitignore" ]; then
    if grep -q "venv/" .gitignore && grep -q ".env" .gitignore; then
        print_success ".gitignore looks good"
    else
        print_warning ".gitignore may be missing important entries"
    fi
else
    print_warning ".gitignore not found"
fi
echo ""

echo "7. Checking for test files..."
echo "----------------------------------------"
if [ -d "tests" ] && [ -f "tests/test_api.py" ]; then
    print_success "Test files found"
else
    print_warning "No test files found"
fi
echo ""

echo "8. Running tests..."
echo "----------------------------------------"
if [ -d "venv" ]; then
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    fi
fi

if command -v pytest &> /dev/null; then
    if pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_output.txt; then
        print_success "All tests passed"
    else
        print_error "Some tests failed"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
else
    print_warning "pytest not found. Install with: pip install pytest httpx"
    print_info "Skipping test execution"
fi
echo ""

echo "9. Checking Scalingo remote..."
echo "----------------------------------------"
if git remote | grep -q "scalingo"; then
    print_success "Scalingo remote configured"
    SCALINGO_URL=$(git remote get-url scalingo 2>/dev/null || echo "")
    print_info "Remote URL: $SCALINGO_URL"
else
    print_warning "Scalingo remote not found"
    print_info "Configure with: scalingo link <app-name>"
fi
echo ""

echo "10. Summary..."
echo "=========================================="
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready for deployment.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. git add ."
    echo "  2. git commit -m 'Your commit message'"
    echo "  3. git push origin main  (optional, for backup)"
    echo "  4. git push scalingo main"
    echo "  5. scalingo status"
    echo "  6. scalingo logs --lines 50"
    exit 0
else
    echo -e "${RED}❌ $FAILED_CHECKS check(s) failed. Please fix issues before deploying.${NC}"
    echo ""
    echo "Review the errors above and fix them before proceeding with deployment."
    exit 1
fi

