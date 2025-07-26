# trippleCheck - Build Automation
.PHONY: help install build test clean dev frontend backend format lint docker

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON_VERSION := 3.11
NODE_VERSION := 18
VENV_PATH := venv
BACKEND_PATH := fastapi_app
FRONTEND_PATH := frontend

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)trippleCheck Build System$(NC)"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then python3 -m venv $(VENV_PATH); fi
	@. $(VENV_PATH)/bin/activate && pip install --upgrade pip
	@. $(VENV_PATH)/bin/activate && pip install -r $(BACKEND_PATH)/requirements_dev.txt
	@. $(VENV_PATH)/bin/activate && pip install pytest pytest-cov black isort mypy
	@cd $(FRONTEND_PATH) && npm install
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

build: install ## Build the application
	@echo "$(BLUE)Building application...$(NC)"
	@cd $(FRONTEND_PATH) && npm run build
	@echo "$(GREEN)Build completed successfully!$(NC)"

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@. $(VENV_PATH)/bin/activate && pytest $(BACKEND_PATH)/tests/ -v
	@cd $(FRONTEND_PATH) && npm run check
	@echo "$(GREEN)All tests passed!$(NC)"

test-coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@. $(VENV_PATH)/bin/activate && pytest $(BACKEND_PATH)/tests/ --cov=$(BACKEND_PATH) --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

lint: ## Run linting and type checking
	@echo "$(BLUE)Running linting...$(NC)"
	@. $(VENV_PATH)/bin/activate && black --check $(BACKEND_PATH)/
	@. $(VENV_PATH)/bin/activate && isort --check-only $(BACKEND_PATH)/
	@. $(VENV_PATH)/bin/activate && mypy $(BACKEND_PATH)/
	@cd $(FRONTEND_PATH) && npm run check
	@echo "$(GREEN)Linting completed successfully!$(NC)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@. $(VENV_PATH)/bin/activate && black $(BACKEND_PATH)/
	@. $(VENV_PATH)/bin/activate && isort $(BACKEND_PATH)/
	@echo "$(GREEN)Code formatted successfully!$(NC)"

dev: ## Start development servers (requires 2 terminals)
	@echo "$(YELLOW)Starting development servers...$(NC)"
	@echo "$(BLUE)Run the following in separate terminals:$(NC)"
	@echo "  $(GREEN)make backend$(NC)  # Terminal 1"
	@echo "  $(GREEN)make frontend$(NC) # Terminal 2"

backend: ## Start backend development server
	@echo "$(BLUE)Starting FastAPI backend...$(NC)"
	@. $(VENV_PATH)/bin/activate && cd $(BACKEND_PATH) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start frontend development server
	@echo "$(BLUE)Starting SvelteKit frontend...$(NC)"
	@cd $(FRONTEND_PATH) && npm run dev

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache/ htmlcov/ .coverage 2>/dev/null || true
	@rm -rf $(FRONTEND_PATH)/.svelte-kit $(FRONTEND_PATH)/build 2>/dev/null || true
	@find . -name "*.tmp" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup completed!$(NC)"

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker build -t tripplecheck-backend -f docker/Dockerfile.backend .
	@docker build -t tripplecheck-frontend -f docker/Dockerfile.frontend .
	@echo "$(GREEN)Docker images built successfully!$(NC)"

docker-up: ## Start application with Docker Compose
	@echo "$(BLUE)Starting application with Docker...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Application started at http://localhost:8000$(NC)"

docker-down: ## Stop Docker containers
	@docker-compose down

production-build: build ## Build for production deployment
	@echo "$(BLUE)Building for production...$(NC)"
	@mkdir -p $(BACKEND_PATH)/app/static/dist
	@cp -r $(FRONTEND_PATH)/build/* $(BACKEND_PATH)/app/static/dist/
	@echo "$(GREEN)Production build completed!$(NC)"

check-env: ## Verify environment configuration
	@echo "$(BLUE)Checking environment...$(NC)"
	@if [ ! -f ".env" ]; then echo "$(RED)Error: .env file not found$(NC)"; exit 1; fi
	@. $(VENV_PATH)/bin/activate && python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
	@cd $(FRONTEND_PATH) && node --version
	@tesseract --version | head -1
	@echo "$(GREEN)Environment check passed!$(NC)"

deploy-check: lint test production-build ## Full deployment readiness check
	@echo "$(BLUE)Running deployment readiness check...$(NC)"
	@make check-env
	@echo "$(GREEN)Deployment check completed successfully!$(NC)"

# CI/CD targets
ci-install: ## Install dependencies for CI
	@pip install --upgrade pip
	@pip install -r $(BACKEND_PATH)/requirements_dev.txt
	@pip install pytest pytest-cov black isort mypy

ci-test: ## Run tests in CI environment
	@black --check $(BACKEND_PATH)/
	@isort --check-only $(BACKEND_PATH)/
	@mypy $(BACKEND_PATH)/
	@pytest $(BACKEND_PATH)/tests/ --cov=$(BACKEND_PATH) --cov-report=xml

# Development utilities
logs: ## View application logs
	@tail -f *.log 2>/dev/null || echo "No log files found"

status: ## Show development server status
	@echo "$(BLUE)Checking server status...$(NC)"
	@curl -s http://localhost:8000/ > /dev/null && echo "$(GREEN)Backend: Running$(NC)" || echo "$(RED)Backend: Not running$(NC)"
	@curl -s http://localhost:5173/ > /dev/null && echo "$(GREEN)Frontend: Running$(NC)" || echo "$(RED)Frontend: Not running$(NC)"