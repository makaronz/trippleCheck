# trippleCheck - Development Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Tesseract OCR (for file processing)

### Environment Setup

1. **Clone and navigate to project**:
   ```bash
   git clone <repository-url>
   cd trippleCheck
   ```

2. **Run setup script**:
   ```bash
   ./dev-scripts.sh setup
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenRouter API key
   ```

4. **Start development servers**:
   ```bash
   # Terminal 1 - Backend
   ./dev-scripts.sh backend
   
   # Terminal 2 - Frontend  
   ./dev-scripts.sh frontend
   ```

## 🛠️ Development Scripts

The `dev-scripts.sh` provides convenient commands for development:

```bash
./dev-scripts.sh setup         # Set up development environment
./dev-scripts.sh backend       # Start FastAPI backend (port 8000)
./dev-scripts.sh frontend      # Start SvelteKit frontend (port 5173)
./dev-scripts.sh test          # Run test suite
./dev-scripts.sh test-coverage # Run tests with coverage report
./dev-scripts.sh lint          # Run code linting
./dev-scripts.sh format        # Format code with black/isort
./dev-scripts.sh clean         # Clean build artifacts
```

## 🏗️ Project Structure

```
trippleCheck/
├── fastapi_app/           # Modern FastAPI backend
│   ├── app/
│   │   ├── main.py        # Application entry point
│   │   ├── routers/       # API route handlers
│   │   ├── services/      # Business logic
│   │   ├── utils/         # Utility functions
│   │   ├── models/        # Pydantic schemas
│   │   └── prompts/       # AI prompt templates
│   ├── requirements_dev.txt # Development dependencies
│   └── tests/             # Test suite
├── frontend/              # SvelteKit frontend
│   ├── src/
│   │   ├── routes/        # Page components
│   │   └── lib/           # Shared components
│   └── package.json
├── .env.example           # Environment variables template
├── dev-scripts.sh         # Development utility scripts
└── pyproject.toml         # Python project configuration
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
./dev-scripts.sh test

# Run with coverage
./dev-scripts.sh test-coverage

# Run specific test file
source venv/bin/activate
pytest fastapi_app/tests/test_file_processor.py -v
```

### Test Structure
- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test API endpoints and components
- **Coverage target**: 80% minimum

## 📝 Code Quality

### Linting and Formatting
```bash
# Check code quality
./dev-scripts.sh lint

# Auto-format code
./dev-scripts.sh format
```

### Tools Used
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Static type checking
- **pytest**: Testing framework

### Code Style Guidelines
- Line length: 100 characters
- Type hints: Required for all functions
- Docstrings: Required for public functions
- Import order: Standard library, third-party, local

## 🔧 Environment Configuration

### Required Environment Variables
```bash
# .env file
OPENROUTER_API_KEY=your_openrouter_api_key_here
APP_URL=http://localhost:8000
APP_TITLE=trippleCheck
```

### Optional Environment Variables
```bash
GOOGLE_API_KEY=your_google_api_key_here  # For verification step
VITE_FASTAPI_URL=http://127.0.0.1:8000   # Frontend API URL
SECRET_KEY=dev-secret-key                 # Session security
```

## 🐛 Debugging

### Backend Debugging
1. Start backend with debug flag:
   ```bash
   source venv/bin/activate
   cd fastapi_app
   uvicorn app.main:app --reload --log-level debug
   ```

2. Access interactive API docs: http://localhost:8000/docs

### Frontend Debugging
1. Start with Vite debug mode:
   ```bash
   cd frontend
   npm run dev -- --debug
   ```

2. Use browser developer tools for debugging

### Common Issues

**"Module not found" errors**:
- Ensure virtual environment is activated
- Run `pip install -r fastapi_app/requirements_dev.txt`

**"Tesseract not found" errors**:
- Install Tesseract OCR: `brew install tesseract` (macOS)
- Verify installation: `tesseract --version`

**Frontend build failures**:
- Clear node_modules: `rm -rf frontend/node_modules`
- Reinstall: `cd frontend && npm install`

## 📚 API Documentation

### FastAPI Backend
- Interactive docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

### Key Endpoints
- `POST /api/v1/process` - Main query processing
- `POST /api/v1/files/process` - File upload and processing
- `GET /` - Frontend SPA serving

## 🔄 AI Pipeline

The application uses a 3-step AI processing pipeline:

1. **Analysis**: Query understanding and context analysis
2. **Perspectives**: Generate multiple viewpoints in parallel
3. **Synthesis**: Verification and final answer creation

### Supported File Types
- Documents: PDF, DOC, DOCX, ODT, RTF, TXT, MD
- Spreadsheets: XLSX, XLS, ODS, CSV
- Presentations: PPTX, PPT, ODP
- Images: JPG, PNG, GIF, BMP, TIFF (with OCR)
- Archives: ZIP, RAR
- Web: HTML, XML, EPUB

## 🚀 Deployment

### Local Production Build
```bash
# Build frontend
cd frontend
npm run build

# Start production server
cd ../fastapi_app
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Render.com Deployment
The project is configured for Render.com deployment using `render.yaml`.

Required environment variables on Render:
- `OPENROUTER_API_KEY`
- `PYTHON_VERSION=3.11.7`

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Create feature branch from `main`
2. Make changes following code style guidelines
3. Add tests for new functionality
4. Run quality checks: `./dev-scripts.sh lint && ./dev-scripts.sh test`
5. Submit pull request

For detailed contribution guidelines, see CONTRIBUTING.md.