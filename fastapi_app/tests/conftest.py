"""
Test configuration and fixtures for trippleCheck backend tests.
"""

import os
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Import the FastAPI app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.utils.dependencies import get_openrouter_api_key


# Test client fixture
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# Mock API key dependency
@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    def mock_get_api_key():
        return "test-api-key"
    
    app.dependency_overrides[get_openrouter_api_key] = mock_get_api_key
    yield "test-api-key"
    app.dependency_overrides.clear()


# Test environment fixtures
@pytest.fixture
def test_env_vars():
    """Set up test environment variables."""
    test_vars = {
        "OPENROUTER_API_KEY": "test-api-key",
        "APP_URL": "http://localhost:8000",
        "APP_TITLE": "trippleCheck Test"
    }
    
    # Store original values
    original_vars = {}
    for key, value in test_vars.items():
        original_vars[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original values
    for key, original_value in original_vars.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


# File testing fixtures
@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Test content for file processing")
        temp_path = tmp.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"


@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return "This is a test document with some sample text content."


@pytest.fixture
def sample_image_content():
    """Sample image content for testing."""
    # Simple 1x1 PNG image in bytes
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13'
        b'\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc'
        b'\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )


# Mock external services
@pytest.fixture
def mock_openrouter_api():
    """Mock OpenRouter API calls."""
    with patch('fastapi_app.app.utils.openrouter_client.call_openrouter_api_async') as mock:
        mock.return_value = "Mocked AI response"
        yield mock


@pytest.fixture
def mock_tesseract():
    """Mock Tesseract OCR calls."""
    with patch('pytesseract.image_to_string') as mock:
        mock.return_value = "Extracted text from image"
        yield mock


@pytest.fixture
def mock_pymupdf():
    """Mock PyMuPDF PDF processing."""
    with patch('fitz.open') as mock:
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Extracted text from PDF"
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock.return_value = mock_doc
        yield mock


# Test data fixtures
@pytest.fixture
def sample_process_request():
    """Sample process query request data."""
    return {
        "query": "What are the benefits of AI in healthcare?",
        "documents": [
            {
                "name": "test.txt",
                "content": "AI in healthcare can improve diagnosis accuracy.",
                "size": 45
            }
        ]
    }


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for testing."""
    return {
        "main_topics": ["AI", "healthcare"],
        "user_intent": "Understanding AI benefits in healthcare",
        "complexity": "medium",
        "required_knowledge": ["healthcare", "AI technology"],
        "suggested_tools": ["medical databases", "AI research papers"],
        "potential_challenges": ["data privacy", "implementation costs"],
        "analysis_summary": "Query seeks comprehensive understanding of AI applications in healthcare sector."
    }


# Performance testing fixtures
@pytest.fixture
def benchmark_data():
    """Data for performance benchmarking."""
    return {
        "small_file": "A" * 1000,          # 1KB
        "medium_file": "B" * 100000,       # 100KB
        "large_file": "C" * 1000000,       # 1MB
    }


# Database testing fixtures (for future use)
@pytest.fixture
def test_db():
    """Test database fixture (placeholder for future database integration)."""
    # This would set up a test database when/if we add database support
    pass


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "file_processing: mark test as file processing test"
    )


# Test collection modifiers
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "test_file_processor" in str(item.fspath):
            item.add_marker(pytest.mark.file_processing)