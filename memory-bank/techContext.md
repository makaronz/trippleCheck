# Technical Context - trippleCheck AI Agent

## Technology Stack Overview

### Frontend Stack
- **Framework**: SvelteKit 2.0+
- **Language**: TypeScript 5.0+
- **Build Tool**: Vite 5.0+
- **Styling**: TailwindCSS 3.0+
- **Testing**: Vitest + Testing Library
- **Package Manager**: npm 9.0+

### Backend Stack
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.8+
- **Runtime**: ASGI (Uvicorn/Gunicorn)
- **Validation**: Pydantic 2.0+
- **Testing**: pytest + httpx
- **Package Manager**: pip + requirements.txt

### Infrastructure Stack
- **Hosting**: Render.com
- **Process Manager**: Gunicorn
- **Reverse Proxy**: Nginx (managed by Render)
- **CDN**: Cloudflare (via Render)
- **Monitoring**: Render built-in + custom logging

## Development Environment Setup

### Prerequisites Installation

#### macOS (Current Environment)
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.8+
brew install python@3.11

# Install Node.js 16+
brew install node@18

# Install Tesseract OCR
brew install tesseract

# Install LibreOffice (optional)
brew install --cask libreoffice

# Install Unrar (optional)
brew install unrar
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python 3.8+
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js 16+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install Tesseract OCR
sudo apt install tesseract-ocr tesseract-ocr-eng

# Install LibreOffice (optional)
sudo apt install libreoffice

# Install Unrar (optional)
sudo apt install unrar
```

#### Windows
```bash
# Install Python 3.8+ from python.org
# Install Node.js 16+ from nodejs.org
# Install Tesseract from UB-Mannheim GitHub releases
# Install LibreOffice from libreoffice.org
# Install Unrar from rarlab.com
```

### Project Setup Commands

#### Backend Setup
```bash
# Navigate to project root
cd trippleCheck

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r fastapi_app/requirements.txt

# Verify installation
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Verify installation
npm run build

# Return to project root
cd ..
```

#### Environment Configuration
```bash
# Create environment file
cat > .env << EOF
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Development Configuration
VITE_FASTAPI_URL=http://127.0.0.1:8000
PYTHON_VERSION=3.11

# Optional: Google Search API (for verification)
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
EOF
```

## Project Structure & File Organization

### Root Directory Structure
```
trippleCheck/
├── .cursor/                    # Cursor IDE configuration
│   └── rules/                  # Project rules and patterns
├── .github/                    # GitHub workflows and templates
├── app/                        # Legacy Flask app (deprecated)
├── docs/                       # Project documentation
├── fastapi_app/                # Main backend application
│   ├── app/                    # FastAPI application code
│   │   ├── models/             # Data models and schemas
│   │   ├── routers/            # API route handlers
│   │   ├── services/           # Business logic services
│   │   ├── utils/              # Utility functions
│   │   └── prompts/            # AI prompt templates
│   ├── requirements.txt        # Python dependencies
│   └── tests/                  # Backend test suite
├── frontend/                   # SvelteKit frontend application
│   ├── src/                    # Source code
│   │   ├── lib/                # Shared utilities
│   │   └── routes/             # SvelteKit routes
│   ├── static/                 # Static assets
│   ├── package.json            # Node.js dependencies
│   └── svelte.config.js        # SvelteKit configuration
├── memory-bank/                # Project memory and context
├── tasks/                      # Task planning and context
├── .env                        # Environment variables (gitignored)
├── .gitignore                  # Git ignore patterns
├── Procfile                    # Heroku deployment config
├── README.md                   # Project overview
├── render.yaml                 # Render.com deployment config
├── requirements.txt            # Root requirements (legacy)
└── run.py                      # Legacy Flask runner
```

### Key File Locations

#### Backend Core Files
- **Main App**: `fastapi_app/app/main.py`
- **API Routes**: `fastapi_app/app/routers/`
- **Data Models**: `fastapi_app/app/models/`
- **Services**: `fastapi_app/app/services/`
- **File Processing**: `fastapi_app/app/utils/file_processor.py`
- **AI Integration**: `fastapi_app/app/utils/openrouter_client.py`

#### Frontend Core Files
- **Main Page**: `frontend/src/routes/+page.svelte`
- **App Layout**: `frontend/src/app.html`
- **Global Styles**: `frontend/src/app.css`
- **Type Definitions**: `frontend/src/app.d.ts`
- **Build Config**: `frontend/vite.config.ts`

## Dependencies & External Services

### Python Dependencies (Backend)
```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0

# Data Validation & Serialization
pydantic==2.5.0
pydantic-settings==2.1.0

# File Processing
python-magic==0.4.27
PyPDF2==3.0.1
python-docx==1.1.0
Pillow==10.1.0
pytesseract==0.3.10
odfpy==1.4.1
defusedxml==0.7.1

# HTTP Client
httpx==0.25.2
aiofiles==23.2.1

# Utilities
python-multipart==0.0.6
python-dotenv==1.0.0
```

### Node.js Dependencies (Frontend)
```json
{
  "dependencies": {
    "@sveltejs/kit": "^2.0.0",
    "svelte": "^4.2.0",
    "vite": "^5.0.0"
  },
  "devDependencies": {
    "@sveltejs/adapter-auto": "^3.0.0",
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "typescript": "^5.0.0",
    "vitest": "^1.0.0"
  }
}
```

### External Service Dependencies

#### OpenRouter AI API
- **Purpose**: AI model access for analysis and perspective generation
- **Authentication**: API key in `OPENROUTER_API_KEY` environment variable
- **Rate Limits**: Varies by model, typically 1000 requests/hour
- **Models Used**: GPT-4, Claude-3, Gemini Pro
- **Integration**: `fastapi_app/app/utils/openrouter_client.py`

#### Google Search API (Optional)
- **Purpose**: Fact verification and source checking
- **Authentication**: API key + Search Engine ID
- **Rate Limits**: 100 queries/day (free tier)
- **Integration**: `fastapi_app/app/services/verification_service.py`

## Development Workflow

### Local Development Commands

#### Backend Development
```bash
# Start backend server (development mode)
cd fastapi_app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run backend tests
pytest tests/ -v

# Check code formatting
black app/ tests/
isort app/ tests/

# Type checking
mypy app/
```

#### Frontend Development
```bash
# Start frontend development server
cd frontend
npm run dev

# Run frontend tests
npm run test

# Build for production
npm run build

# Preview production build
npm run preview
```

#### Full Stack Development
```bash
# Terminal 1: Backend
cd fastapi_app && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Testing Strategy

#### Backend Testing
```python
# Unit tests for services
pytest fastapi_app/tests/test_services/ -v

# Integration tests for API
pytest fastapi_app/tests/test_api/ -v

# File processing tests
pytest fastapi_app/tests/test_file_processor.py -v

# Coverage report
pytest --cov=app --cov-report=html
```

#### Frontend Testing
```bash
# Component tests
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests (if configured)
npm run test:e2e
```

## Deployment Configuration

### Render.com Deployment

#### Build Configuration (`render.yaml`)
```yaml
services:
  - type: web
    name: trippleCheck
    env: python
    buildCommand: |
      pip install -r fastapi_app/requirements.txt
      cd frontend && npm install && npm run build
      cp -r frontend/build/* fastapi_app/app/static/dist/
    startCommand: cd fastapi_app && gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: OPENROUTER_API_KEY
        sync: false
```

#### Environment Variables (Production)
```bash
# Required
OPENROUTER_API_KEY=your_production_api_key

# Optional
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
```

### Local Production Testing
```bash
# Build frontend
cd frontend && npm run build

# Copy static files
cp -r frontend/build/* fastapi_app/app/static/dist/

# Start production server
cd fastapi_app
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Performance & Optimization

### Backend Performance
- **Async Processing**: All file processing and AI calls are async
- **Connection Pooling**: HTTP clients use connection pooling
- **Memory Management**: Large files processed in chunks
- **Caching**: In-memory caching for processed content

### Frontend Performance
- **Code Splitting**: SvelteKit automatic code splitting
- **Static Assets**: Optimized images and fonts
- **Lazy Loading**: Components loaded on demand
- **Service Worker**: Offline capability (future)

### Monitoring & Logging

#### Application Logging
```python
# Logging configuration
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Usage in services
logger = logging.getLogger(__name__)
logger.info("Processing file: %s", filename)
logger.error("Processing failed: %s", error)
```

#### Performance Monitoring
- **Response Times**: Track API endpoint performance
- **Error Rates**: Monitor processing failures
- **Resource Usage**: CPU and memory utilization
- **External API Calls**: Track OpenRouter and Google API usage

## Security Implementation

### File Security
- **MIME Type Validation**: Verify file types before processing
- **Size Limits**: 10MB per file, 50MB total
- **Content Scanning**: Basic malware detection
- **Secure Storage**: Temporary file handling

### API Security
- **Input Validation**: Pydantic models for all inputs
- **Rate Limiting**: 60 requests per minute per IP
- **CORS Configuration**: Restricted to allowed origins
- **Error Handling**: No sensitive information in error messages

### Environment Security
- **Secret Management**: Environment variables for sensitive data
- **API Key Rotation**: Regular key updates
- **Access Control**: Minimal required permissions
- **Audit Logging**: Track all file processing activities

## Troubleshooting Guide

### Common Issues

#### Backend Issues
```bash
# Port already in use
lsof -ti:8000 | xargs kill -9

# Virtual environment issues
rm -rf venv && python3 -m venv venv

# Dependency conflicts
pip install --upgrade pip
pip install -r fastapi_app/requirements.txt --force-reinstall
```

#### Frontend Issues
```bash
# Node modules corrupted
rm -rf node_modules package-lock.json
npm install

# Build failures
npm run build --verbose

# Development server issues
npm run dev -- --host 0.0.0.0
```

#### File Processing Issues
```bash
# Tesseract not found
brew install tesseract  # macOS
sudo apt install tesseract-ocr  # Linux

# Permission issues
chmod +x /usr/local/bin/tesseract

# Memory issues with large files
# Reduce file size or implement streaming
```

### Debug Commands
```bash
# Check Python version
python3 --version

# Check Node.js version
node --version

# Check Tesseract installation
tesseract --version

# Check system resources
top -l 1 | head -10  # macOS
htop  # Linux

# Check network connectivity
curl -I http://localhost:8000/health
```

## Future Technical Considerations

### Planned Upgrades
- **Python 3.12**: Performance improvements and new features
- **SvelteKit 2.0**: Enhanced performance and developer experience
- **FastAPI 0.105+**: Latest features and security updates
- **TypeScript 5.0+**: Enhanced type safety

### Scalability Improvements
- **Database Integration**: PostgreSQL for persistent storage
- **Redis Caching**: Distributed caching for better performance
- **Message Queue**: Celery + Redis for background processing
- **Load Balancing**: Multiple backend instances

### Security Enhancements
- **JWT Authentication**: User session management
- **API Rate Limiting**: Per-user rate limiting
- **File Encryption**: Encrypted file storage
- **Audit Trail**: Comprehensive activity logging 