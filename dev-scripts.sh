#!/bin/bash

# trippleCheck Development Scripts
# Usage: ./dev-scripts.sh [command]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
BACKEND_PATH="$PROJECT_ROOT/fastapi_app"
FRONTEND_PATH="$PROJECT_ROOT/frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        log_error "Virtual environment not found. Run './dev-scripts.sh setup' first."
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    source "$VENV_PATH/bin/activate"
}

# Commands
setup() {
    log_info "Setting up development environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv "$VENV_PATH"
    fi
    
    # Activate and install backend dependencies
    log_info "Installing backend dependencies..."
    activate_venv
    pip install --upgrade pip
    pip install -r "$BACKEND_PATH/requirements_dev.txt"
    
    # Install development tools
    pip install pytest pytest-cov black isort mypy
    
    # Install frontend dependencies
    log_info "Installing frontend dependencies..."
    cd "$FRONTEND_PATH"
    npm install
    cd "$PROJECT_ROOT"
    
    log_success "Development environment setup complete!"
    log_info "Don't forget to set your API keys in .env file"
}

backend() {
    check_venv
    log_info "Starting FastAPI backend server..."
    activate_venv
    cd "$BACKEND_PATH"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

frontend() {
    log_info "Starting SvelteKit frontend server..."
    cd "$FRONTEND_PATH"
    npm run dev
}

test() {
    check_venv
    log_info "Running tests..."
    activate_venv
    cd "$PROJECT_ROOT"
    pytest
}

test-coverage() {
    check_venv
    log_info "Running tests with coverage..."
    activate_venv
    cd "$PROJECT_ROOT"
    pytest --cov-report=html
    log_success "Coverage report generated in htmlcov/"
}

lint() {
    check_venv
    log_info "Running linting..."
    activate_venv
    cd "$PROJECT_ROOT"
    
    log_info "Running black..."
    black --check fastapi_app/
    
    log_info "Running isort..."
    isort --check-only fastapi_app/
    
    log_info "Running mypy..."
    mypy fastapi_app/
    
    log_success "Linting complete!"
}

format() {
    check_venv
    log_info "Formatting code..."
    activate_venv
    cd "$PROJECT_ROOT"
    
    log_info "Running black..."
    black fastapi_app/
    
    log_info "Running isort..."
    isort fastapi_app/
    
    log_success "Code formatting complete!"
}

clean() {
    log_info "Cleaning up build artifacts..."
    
    # Python
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -rf .pytest_cache/ htmlcov/ .coverage 2>/dev/null || true
    
    # Frontend
    rm -rf "$FRONTEND_PATH/.svelte-kit" "$FRONTEND_PATH/build" 2>/dev/null || true
    
    # Temporary files
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.temp" -delete 2>/dev/null || true
    
    log_success "Cleanup complete!"
}

help() {
    echo "trippleCheck Development Scripts"
    echo ""
    echo "Available commands:"
    echo "  setup         - Set up development environment"
    echo "  backend       - Start FastAPI backend server"
    echo "  frontend      - Start SvelteKit frontend server"
    echo "  test          - Run tests"
    echo "  test-coverage - Run tests with coverage report"
    echo "  lint          - Run code linting"
    echo "  format        - Format code"
    echo "  clean         - Clean build artifacts"
    echo "  help          - Show this help"
    echo ""
    echo "Example usage:"
    echo "  ./dev-scripts.sh setup"
    echo "  ./dev-scripts.sh backend"
    echo "  ./dev-scripts.sh frontend"
}

# Main script logic
case "${1:-help}" in
    setup)
        setup
        ;;
    backend)
        backend
        ;;
    frontend)
        frontend
        ;;
    test)
        test
        ;;
    test-coverage)
        test-coverage
        ;;
    lint)
        lint
        ;;
    format)
        format
        ;;
    clean)
        clean
        ;;
    help|*)
        help
        ;;
esac