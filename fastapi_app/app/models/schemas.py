from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DocumentInput(BaseModel):
    """Model dla pojedynczego dokumentu wejściowego."""
    name: str
    content: str # Przetworzona treść tekstowa
    size: int # Rozmiar w bajtach

class ProcessQueryRequest(BaseModel):
    """Model dla żądania do endpointu /process_query."""
    query: str = Field(..., description="Zapytanie użytkownika.")
    # Usunięto pole api_key, będzie pobierane ze zmiennych środowiskowych serwera
    documents: Optional[List[DocumentInput]] = Field(None, description="Lista przetworzonych dokumentów jako kontekst.")

class AnalysisResult(BaseModel):
    """Model dla wyniku kroku analizy."""
    model: str
    prompt: str
    result_json: Optional[Dict[str, Any]] = None # Sparsowany JSON
    raw_response: str
    error: Optional[str] = None

class PerspectiveResult(BaseModel):
    """Model dla wyniku pojedynczej perspektywy."""
    type: str # Np. "Informative", "Contrarian", "Complementary"
    model: str
    prompt: str
    response: str # Odpowiedź w formacie Markdown
    error: Optional[str] = None

class VerificationSynthesisResult(BaseModel):
    """Model dla wyniku kroku weryfikacji i syntezy."""
    model: str
    prompt: str
    verification_comparison_report: Optional[str] = None # Raport w Markdown
    final_synthesized_answer: Optional[str] = None # Finalna odpowiedź w Markdown
    raw_response: str
    error: Optional[str] = None

class ProcessQueryResponse(BaseModel):
    """Model dla odpowiedzi z endpointu /process_query."""
    query: str
    timestamp: str
    analysis: AnalysisResult
    perspectives: List[PerspectiveResult]
    verification_synthesis: VerificationSynthesisResult
    # Można dodać pole na metadane dokumentów, jeśli potrzebne

class FileProcessingRequest(BaseModel):
    """Model dla żądania do endpointu /process_file."""
    filename: str
    file_data_base64: str

class FileProcessingResponse(BaseModel):
    """Model dla odpowiedzi z endpointu /process_file."""
    content: str
    error: Optional[str] = None

class ErrorResponse(BaseModel):
    """Model dla odpowiedzi błędu."""
    error: str
