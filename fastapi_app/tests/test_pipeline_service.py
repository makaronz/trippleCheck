"""
Test cases for the AI pipeline service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import pipeline_service
from app.models import schemas


class TestAnalysisStep:
    """Test the analysis step of the pipeline."""

    @patch('app.services.pipeline_service.call_openrouter_api_async')
    async def test_run_analysis_step_success(self, mock_api):
        """Test successful analysis step."""
        # Mock successful API response with valid JSON
        mock_api.return_value = '''
        {
            "main_topics": ["AI", "healthcare"],
            "user_intent": "Understanding AI benefits",
            "complexity": "medium",
            "required_knowledge": ["healthcare", "AI"],
            "suggested_tools": ["research papers"],
            "potential_challenges": ["data privacy"],
            "analysis_summary": "Query about AI in healthcare"
        }
        '''
        
        result = await pipeline_service.run_analysis_step(
            "test-api-key",
            "How can AI help in healthcare?",
            "No documents provided"
        )
        
        assert isinstance(result, schemas.AnalysisResult)
        assert result.model == "openchat/openchat-3.5-0106"
        assert result.result_json is not None
        assert result.result_json["main_topics"] == ["AI", "healthcare"]
        assert result.error is None

    @patch('app.services.pipeline_service.call_openrouter_api_async')
    async def test_run_analysis_step_invalid_json(self, mock_api):
        """Test analysis step with invalid JSON response."""
        # Mock API response with invalid JSON
        mock_api.return_value = "This is not valid JSON"
        
        result = await pipeline_service.run_analysis_step(
            "test-api-key",
            "Test query",
            "No documents"
        )
        
        assert isinstance(result, schemas.AnalysisResult)
        assert result.result_json is None
        assert result.error is not None
        assert "JSON" in result.error

    @patch('app.services.pipeline_service.call_openrouter_api_async')
    async def test_run_analysis_step_api_error(self, mock_api):
        """Test analysis step with API error."""
        # Mock API error
        mock_api.side_effect = Exception("API connection failed")
        
        result = await pipeline_service.run_analysis_step(
            "test-api-key",
            "Test query",
            "No documents"
        )
        
        assert isinstance(result, schemas.AnalysisResult)
        assert result.result_json is None
        assert result.error is not None
        assert "API connection failed" in result.error


class TestPerspectiveGeneration:
    """Test the perspective generation step."""

    @patch('app.services.pipeline_service.call_openrouter_api_async')
    async def test_run_perspective_generation_step_success(self, mock_api):
        """Test successful perspective generation."""
        # Mock API responses for all three perspectives
        mock_api.side_effect = [
            "Informative perspective response",
            "Contrarian perspective response",
            "Complementary perspective response"
        ]
        
        # Create mock analysis result
        analysis_result = schemas.AnalysisResult(
            model="test-model",
            prompt="test-prompt",
            result_json={"analysis_summary": "Test analysis"},
            raw_response="test response",
            error=None
        )
        
        results = await pipeline_service.run_perspective_generation_step(
            "test-api-key",
            "Test query",
            analysis_result,
            "Test documents"
        )
        
        assert len(results) == 3
        assert all(isinstance(r, schemas.PerspectiveResult) for r in results)
        
        types = [r.type for r in results]
        assert "Informative" in types
        assert "Contrarian" in types
        assert "Complementary" in types
        
        # Check that all perspectives succeeded
        assert all(r.error is None for r in results)

    @patch('app.services.pipeline_service.call_openrouter_api_async')
    async def test_run_perspective_generation_step_partial_failure(self, mock_api):
        """Test perspective generation with some failures."""
        # Mock API responses with one failure
        mock_api.side_effect = [
            "Informative perspective response",
            Exception("API error for contrarian"),
            "Complementary perspective response"
        ]
        
        analysis_result = schemas.AnalysisResult(
            model="test-model",
            prompt="test-prompt",
            result_json={"analysis_summary": "Test analysis"},
            raw_response="test response",
            error=None
        )
        
        results = await pipeline_service.run_perspective_generation_step(
            "test-api-key",
            "Test query",
            analysis_result,
            "Test documents"
        )
        
        assert len(results) == 3
        
        # Check that one perspective failed
        errors = [r.error for r in results]
        assert errors.count(None) == 2  # Two successes
        assert any("API error for contrarian" in str(e) for e in errors if e)

    async def test_call_perspective_model_success(self):
        """Test individual perspective model call."""
        with patch('app.services.pipeline_service.call_openrouter_api_async') as mock_api:
            mock_api.return_value = "Test perspective response"
            
            result = await pipeline_service._call_perspective_model(
                "test-api-key",
                "test-model",
                "test-prompt",
                "Informative"
            )
            
            assert isinstance(result, schemas.PerspectiveResult)
            assert result.type == "Informative"
            assert result.model == "test-model"
            assert result.response == "Test perspective response"
            assert result.error is None


class TestVerificationSynthesis:
    """Test the verification and synthesis step."""

    @patch('app.services.pipeline_service.call_openrouter_api_async')
    async def test_run_verification_synthesis_step_success(self, mock_api):
        """Test successful verification and synthesis."""
        # Mock API response with proper format
        mock_api.return_value = """
        ## Verification and Comparison Report
        All perspectives are valid and well-reasoned.
        
        ## Final Synthesized Answer
        This is the final synthesized answer combining all perspectives.
        """
        
        # Create mock inputs
        analysis_result = schemas.AnalysisResult(
            model="test-model",
            prompt="test-prompt",
            result_json={"analysis_summary": "Test analysis"},
            raw_response="test response",
            error=None
        )
        
        perspectives = [
            schemas.PerspectiveResult(
                type="Informative",
                model="model1",
                prompt="prompt1",
                response="Informative response",
                error=None
            ),
            schemas.PerspectiveResult(
                type="Contrarian",
                model="model2",
                prompt="prompt2",
                response="Contrarian response",
                error=None
            ),
            schemas.PerspectiveResult(
                type="Complementary",
                model="model3",
                prompt="prompt3",
                response="Complementary response",
                error=None
            )
        ]
        
        result = await pipeline_service.run_verification_synthesis_step(
            "test-api-key",
            "Test query",
            analysis_result,
            perspectives
        )
        
        assert isinstance(result, schemas.VerificationSynthesisResult)
        assert result.error is None
        assert "All perspectives are valid" in result.verification_comparison_report
        assert "final synthesized answer" in result.final_synthesized_answer

    async def test_run_verification_synthesis_step_insufficient_perspectives(self):
        """Test verification with insufficient perspectives."""
        analysis_result = schemas.AnalysisResult(
            model="test-model",
            prompt="test-prompt",
            result_json={"analysis_summary": "Test analysis"},
            raw_response="test response",
            error=None
        )
        
        # Only provide 2 perspectives instead of 3
        perspectives = [
            schemas.PerspectiveResult(
                type="Informative",
                model="model1",
                prompt="prompt1",
                response="Informative response",
                error=None
            ),
            schemas.PerspectiveResult(
                type="Contrarian",
                model="model2",
                prompt="prompt2",
                response="Contrarian response",
                error=None
            )
        ]
        
        result = await pipeline_service.run_verification_synthesis_step(
            "test-api-key",
            "Test query",
            analysis_result,
            perspectives
        )
        
        assert isinstance(result, schemas.VerificationSynthesisResult)
        assert result.error is not None
        assert "Not all 3 perspectives" in result.error

    async def test_run_verification_synthesis_step_with_perspective_errors(self):
        """Test verification when perspectives contain errors."""
        analysis_result = schemas.AnalysisResult(
            model="test-model",
            prompt="test-prompt",
            result_json={"analysis_summary": "Test analysis"},
            raw_response="test response",
            error=None
        )
        
        perspectives = [
            schemas.PerspectiveResult(
                type="Informative",
                model="model1",
                prompt="prompt1",
                response="Informative response",
                error=None
            ),
            schemas.PerspectiveResult(
                type="Contrarian",
                model="model2",
                prompt="prompt2",
                response="Error response",
                error="API error occurred"
            ),
            schemas.PerspectiveResult(
                type="Complementary",
                model="model3",
                prompt="prompt3",
                response="Complementary response",
                error=None
            )
        ]
        
        result = await pipeline_service.run_verification_synthesis_step(
            "test-api-key",
            "Test query",
            analysis_result,
            perspectives
        )
        
        assert isinstance(result, schemas.VerificationSynthesisResult)
        assert result.error is not None
        assert "contain an error" in result.error


class TestFullPipeline:
    """Test the complete AI pipeline."""

    @patch('app.services.pipeline_service.run_verification_synthesis_step')
    @patch('app.services.pipeline_service.run_perspective_generation_step')
    @patch('app.services.pipeline_service.run_analysis_step')
    async def test_run_ai_pipeline_success(self, mock_analysis, mock_perspectives, mock_synthesis):
        """Test successful complete AI pipeline."""
        # Mock all pipeline steps
        mock_analysis.return_value = schemas.AnalysisResult(
            model="analysis-model",
            prompt="analysis-prompt",
            result_json={"analysis_summary": "Test analysis"},
            raw_response="analysis response",
            error=None
        )
        
        mock_perspectives.return_value = [
            schemas.PerspectiveResult(
                type="Informative",
                model="model1",
                prompt="prompt1",
                response="Informative response",
                error=None
            ),
            schemas.PerspectiveResult(
                type="Contrarian",
                model="model2",
                prompt="prompt2",
                response="Contrarian response",
                error=None
            ),
            schemas.PerspectiveResult(
                type="Complementary",
                model="model3",
                prompt="prompt3",
                response="Complementary response",
                error=None
            )
        ]
        
        mock_synthesis.return_value = schemas.VerificationSynthesisResult(
            model="synthesis-model",
            prompt="synthesis-prompt",
            verification_comparison_report="All perspectives valid",
            final_synthesized_answer="Final answer",
            raw_response="synthesis response",
            error=None
        )
        
        # Create request
        request = schemas.ProcessQueryRequest(
            query="Test query",
            documents=[
                schemas.DocumentInput(
                    name="test.txt",
                    content="Test document content",
                    size=100
                )
            ]
        )
        
        result = await pipeline_service.run_ai_pipeline(request, "test-api-key")
        
        assert isinstance(result, schemas.ProcessQueryResponse)
        assert result.query == "Test query"
        assert result.analysis.error is None
        assert len(result.perspectives) == 3
        assert result.verification_synthesis.error is None
        
        # Verify all steps were called
        mock_analysis.assert_called_once()
        mock_perspectives.assert_called_once()
        mock_synthesis.assert_called_once()

    @patch('app.services.pipeline_service.run_analysis_step')
    async def test_run_ai_pipeline_with_analysis_error(self, mock_analysis):
        """Test pipeline with analysis step error."""
        # Mock analysis step with error
        mock_analysis.return_value = schemas.AnalysisResult(
            model="analysis-model",
            prompt="analysis-prompt",
            result_json=None,
            raw_response="error response",
            error="Analysis failed"
        )
        
        request = schemas.ProcessQueryRequest(
            query="Test query",
            documents=[]
        )
        
        result = await pipeline_service.run_ai_pipeline(request, "test-api-key")
        
        assert isinstance(result, schemas.ProcessQueryResponse)
        assert result.analysis.error == "Analysis failed"
        # Verify pipeline continues despite analysis error
        assert result.perspectives is not None
        assert result.verification_synthesis is not None