from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DocumentInput(BaseModel):
    """Model for a single input document."""
    name: str
    content: str # Processed text content
    size: int # Size in bytes

class ProcessQueryRequest(BaseModel):
    """Model for the /process_query endpoint request."""
    query: str = Field(..., description="User's query.")
    # Removed api_key field, it will be retrieved from server environment variables
    documents: Optional[List[DocumentInput]] = Field(None, description="List of processed documents as context.")

class AnalysisResult(BaseModel):
    """Model for the analysis step result."""
    model: str
    prompt: str
    result_json: Optional[Dict[str, Any]] = None # Parsed JSON
    raw_response: str
    error: Optional[str] = None

class PerspectiveResult(BaseModel):
    """Model for a single perspective result."""
    type: str # E.g., "Informative", "Contrarian", "Complementary"
    model: str
    prompt: str
    response: str # Response in Markdown format
    error: Optional[str] = None

class VerificationSynthesisResult(BaseModel):
    """Model for the verification and synthesis step result."""
    model: str
    prompt: str
    verification_comparison_report: Optional[str] = None # Report in Markdown
    final_synthesized_answer: Optional[str] = None # Final answer in Markdown
    raw_response: str
    error: Optional[str] = None

class ProcessQueryResponse(BaseModel):
    """Model for the /process_query endpoint response."""
    query: str
    timestamp: str
    analysis: AnalysisResult
    perspectives: List[PerspectiveResult]
    verification_synthesis: VerificationSynthesisResult
    # Could add a field for document metadata if needed

class FileProcessingRequest(BaseModel):
    """Model for the /process_file endpoint request."""
    filename: str
    file_data_base64: str

class FileProcessingResponse(BaseModel):
    """Model for the /process_file endpoint response."""
    content: str
    error: Optional[str] = None

class ErrorResponse(BaseModel):
    """Model for an error response."""
    error: str
