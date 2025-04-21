from pydantic import BaseModel, Field

class FileProcessingRequest(BaseModel):
    """
    Model for file processing request
    """
    filename: str = Field(..., description="Name of the file being processed")
    content: str = Field(..., description="Base64 encoded content of the file")

class FileProcessingResponse(BaseModel):
    """
    Model for file processing response
    """
    success: bool = Field(..., description="Whether the processing was successful")
    filename: str = Field(..., description="Name of the processed file")
    mime_type: str = Field(..., description="MIME type of the processed file")
    processed_content: str = Field(..., description="Processed content of the file") 