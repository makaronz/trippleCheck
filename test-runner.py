#!/usr/bin/env python3
"""
Simple test runner that bypasses pytest plugin conflicts.
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def run_unit_tests():
    """Run unit tests using a simple approach."""
    print("🧪 Running unit tests...")
    
    # Add fastapi_app to Python path
    project_root = Path(__file__).parent
    fastapi_path = project_root / "fastapi_app"
    sys.path.insert(0, str(fastapi_path))
    
    try:
        # Import and test basic functionality
        from app.main import app
        from app.utils.file_processor import safe_extract_text_from_txt
        from app.models.schemas import ProcessQueryRequest
        
        print("✅ Basic imports successful")
        
        # Test basic functionality
        test_text = safe_extract_text_from_txt(b"Hello, World!")
        assert test_text == "Hello, World!", f"Expected 'Hello, World!', got '{test_text}'"
        print("✅ Text processing test passed")
        
        # Test schema validation
        request = ProcessQueryRequest(query="Test query", documents=[])
        assert request.query == "Test query"
        print("✅ Schema validation test passed")
        
        # Test FastAPI app creation
        assert app is not None
        print("✅ FastAPI app creation test passed")
        
        print("✅ All unit tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Unit test failed: {e}")
        return False

def run_integration_tests():
    """Run integration tests."""
    print("🔗 Running integration tests...")
    
    try:
        from fastapi.testclient import TestClient
        sys.path.insert(0, str(Path(__file__).parent / "fastapi_app"))
        from app.main import app
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        print(f"✅ Root endpoint test: status {response.status_code}")
        
        # Test invalid endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404
        print("✅ 404 handling test passed")
        
        print("✅ All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def run_frontend_tests():
    """Run frontend tests."""
    print("🎨 Running frontend tests...")
    
    try:
        # Change to frontend directory
        frontend_dir = Path(__file__).parent / "frontend"
        os.chdir(frontend_dir)
        
        # Run SvelteKit check
        result = subprocess.run(["npm", "run", "check"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SvelteKit type checking passed")
        else:
            print(f"❌ SvelteKit check failed: {result.stderr}")
            return False
            
        # Test build process
        result = subprocess.run(["npm", "run", "build"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Frontend build test passed")
        else:
            print(f"❌ Frontend build failed: {result.stderr}")
            return False
            
        print("✅ All frontend tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False
    finally:
        # Return to project root
        os.chdir(Path(__file__).parent)

def main():
    """Run all tests."""
    print("🧪 trippleCheck Test Suite")
    print("=" * 50)
    
    results = {
        "Unit Tests": run_unit_tests(),
        "Integration Tests": run_integration_tests(), 
        "Frontend Tests": run_frontend_tests()
    }
    
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed successfully!")
        return 0
    else:
        print("⚠️  Some tests failed. Check output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())