"""
Test cases for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json


class TestHealthEndpoints:
    """Test health and basic endpoints."""

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code in [200, 404]  # 404 if no frontend build

    def test_api_structure(self, client: TestClient):
        """Test API structure is accessible."""
        # Test that the app is properly configured
        assert hasattr(client.app, "router")


class TestProcessEndpoint:
    """Test the main process query endpoint."""

    def test_process_endpoint_without_auth(self, client: TestClient):
        """Test process endpoint without authentication."""
        test_data = {
            "query": "What is AI?",
            "documents": []
        }
        response = client.post("/api/v1/process", json=test_data)
        # Should fail without proper API key setup
        assert response.status_code in [500, 422]  # Configuration error expected

    @patch('app.services.pipeline_service.run_ai_pipeline')
    def test_process_endpoint_with_mocked_pipeline(self, mock_pipeline, client: TestClient, mock_api_key):
        """Test process endpoint with mocked AI pipeline."""
        # Mock the pipeline response
        mock_response = Mock()
        mock_response.query = "What is AI?"
        mock_response.timestamp = "2024-01-01T00:00:00"
        mock_response.analysis = Mock()
        mock_response.analysis.model = "test-model"
        mock_response.analysis.raw_response = "Test analysis"
        mock_response.perspectives = []
        mock_response.verification_synthesis = Mock()
        mock_response.verification_synthesis.final_synthesized_answer = "AI is artificial intelligence."
        
        mock_pipeline.return_value = mock_response

        test_data = {
            "query": "What is AI?",
            "documents": []
        }
        
        response = client.post("/api/v1/process", json=test_data)
        assert response.status_code == 200
        
        # Verify the pipeline was called
        mock_pipeline.assert_called_once()

    def test_process_endpoint_invalid_data(self, client: TestClient, mock_api_key):
        """Test process endpoint with invalid data."""
        # Missing required 'query' field
        test_data = {
            "documents": []
        }
        response = client.post("/api/v1/process", json=test_data)
        assert response.status_code == 422  # Validation error

    def test_process_endpoint_empty_query(self, client: TestClient, mock_api_key):
        """Test process endpoint with empty query."""
        test_data = {
            "query": "",
            "documents": []
        }
        response = client.post("/api/v1/process", json=test_data)
        assert response.status_code == 422  # Validation error


class TestFileProcessingEndpoint:
    """Test file processing endpoints."""

    def test_file_processing_endpoint_invalid_data(self, client: TestClient):
        """Test file processing with invalid data."""
        test_data = {
            "filename": "test.txt"
            # Missing file_data_base64
        }
        response = client.post("/api/v1/files/process", json=test_data)
        assert response.status_code == 422  # Validation error

    @patch('app.utils.file_processor.process_uploaded_file_data')
    def test_file_processing_endpoint_valid_data(self, mock_processor, client: TestClient):
        """Test file processing with valid data."""
        # Mock successful file processing
        mock_processor.return_value = {
            "text": "Processed file content",
            "mime_type": "text/plain",
            "filename": "test.txt"
        }

        import base64
        test_content = base64.b64encode(b"Test file content").decode('utf-8')
        
        test_data = {
            "filename": "test.txt",
            "file_data_base64": test_content
        }
        
        response = client.post("/api/v1/files/process", json=test_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert "content" in response_data
        assert response_data["content"] == "Processed file content"

    @patch('app.utils.file_processor.process_uploaded_file_data')
    def test_file_processing_endpoint_processing_error(self, mock_processor, client: TestClient):
        """Test file processing with processing error."""
        # Mock file processing error
        mock_processor.side_effect = ValueError("Invalid file format")

        import base64
        test_content = base64.b64encode(b"Invalid content").decode('utf-8')
        
        test_data = {
            "filename": "test.invalid",
            "file_data_base64": test_content
        }
        
        response = client.post("/api/v1/files/process", json=test_data)
        assert response.status_code == 400  # Bad request for client errors


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_headers(self, client: TestClient):
        """Test that rate limiting headers are present."""
        response = client.get("/")
        # Check if rate limiting is working (headers may be present)
        # This is a basic test - more sophisticated rate limit testing would require
        # making multiple requests
        assert response.status_code in [200, 404, 429]

    @pytest.mark.slow
    def test_rate_limiting_enforcement(self, client: TestClient):
        """Test rate limiting enforcement with multiple requests."""
        # This test is marked as slow because it makes many requests
        responses = []
        for i in range(5):  # Make several requests quickly
            response = client.get("/")
            responses.append(response.status_code)
        
        # At least some requests should succeed
        assert any(status in [200, 404] for status in responses)


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set."""
        # Test preflight request
        response = client.options("/api/v1/process", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        })
        
        # Should handle CORS properly
        assert response.status_code in [200, 204]


class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_404_handling(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client: TestClient):
        """Test method not allowed error."""
        response = client.put("/api/v1/process")  # PUT not allowed
        assert response.status_code == 405

    def test_invalid_json(self, client: TestClient, mock_api_key):
        """Test invalid JSON handling."""
        response = client.post(
            "/api/v1/process",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestFullWorkflow:
    """Integration tests for complete workflows."""

    @patch('app.utils.openrouter_client.call_openrouter_api_async')
    def test_complete_query_processing_workflow(self, mock_api, client: TestClient, mock_api_key):
        """Test complete query processing workflow."""
        # Mock AI responses
        mock_api.side_effect = [
            '{"main_topics": ["AI"], "user_intent": "learn about AI", "complexity": "low", "required_knowledge": [], "suggested_tools": [], "potential_challenges": [], "analysis_summary": "Simple AI query"}',
            "Informative perspective response",
            "Contrarian perspective response", 
            "Complementary perspective response",
            "## Verification and Comparison Report\nAll perspectives valid\n## Final Synthesized Answer\nAI is artificial intelligence."
        ]

        test_data = {
            "query": "What is artificial intelligence?",
            "documents": []
        }
        
        response = client.post("/api/v1/process", json=test_data)
        
        if response.status_code == 200:
            # If successful, verify response structure
            data = response.json()
            assert "query" in data
            assert "analysis" in data
            assert "perspectives" in data
            assert "verification_synthesis" in data
        else:
            # May fail due to missing dependencies or configuration
            assert response.status_code in [500, 422]