#!/usr/bin/env python3
"""
Validate that all required dependencies are available.
This script is used in CI/CD to ensure the environment is properly set up.
"""

import sys
import importlib
from typing import List, Tuple

def check_dependencies() -> List[Tuple[str, bool, str]]:
    """Check if all required dependencies are available."""
    # Critical dependencies for the application
    dependencies = [
        ('fastapi', 'FastAPI web framework'),
        ('uvicorn', 'ASGI server'),
        ('pydantic', 'Data validation'),
        ('httpx', 'HTTP client for API calls'),
        ('slowapi', 'Rate limiting'),
        ('python_dotenv', 'Environment variable loading'),
        
        # File processing dependencies
        ('PIL', 'Image processing (Pillow)'),
        ('pytesseract', 'OCR functionality'),
        ('PyMuPDF', 'PDF processing'),
        ('openpyxl', 'Excel file support'),
        ('python_pptx', 'PowerPoint support'),
        ('markdown', 'Markdown processing'),
        ('beautifulsoup4', 'HTML parsing'),
        
        # Testing dependencies (optional in production)
        ('pytest', 'Testing framework'),
    ]
    
    results = []
    for dep, description in dependencies:
        try:
            module = importlib.import_module(dep)
            version = getattr(module, '__version__', 'unknown')
            results.append((dep, True, version))
        except ImportError:
            results.append((dep, False, 'not found'))
    
    return results

def main():
    """Main validation function."""
    print("🔍 Validating Python dependencies...")
    print("=" * 50)
    
    results = check_dependencies()
    missing = []
    
    for dep, available, version in results:
        status = "✅" if available else "❌"
        print(f"{status} {dep:20} {version}")
        if not available:
            missing.append(dep)
    
    print("=" * 50)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Install missing dependencies with:")
        print("pip install -r fastapi_app/requirements.txt")
        return 1
    else:
        print("✅ All dependencies are available!")
        return 0

if __name__ == "__main__":
    sys.exit(main())