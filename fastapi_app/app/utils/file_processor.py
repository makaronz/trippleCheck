# -*- coding: utf-8 -*-
import os
import base64
import tempfile
import traceback
import io
import logging

# File processing dependencies
try:
    import fitz  # type: ignore # PyMuPDF
except ImportError:
    fitz = None

try:
    import ocrmypdf # type: ignore
    # Check if Tesseract is available for ocrmypdf
    # ocrmypdf.check() # Can raise exception if Tesseract is missing
except ImportError:
    ocrmypdf = None
except Exception as ocr_check_e:
     logging.warning(f"ocrmypdf is installed, but there was a problem checking dependencies (e.g., Tesseract): {ocr_check_e}")
     ocrmypdf = None # Treat as unavailable if system dependencies are not met

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None # Handle missing libraries

try:
    import markdown
    from bs4 import BeautifulSoup
except ImportError:
    markdown = None
    BeautifulSoup = None # Handle missing libraries

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants (could be moved to config)
MAX_DOCUMENT_CHARS = 4000 # Max characters returned from a file
MAX_PDF_SIZE_MB = 10  # Max PDF file size in MB
MAX_IMAGE_SIZE_MB = 10 # Max Image file size in MB
MAX_BASE64_SIZE_MB = 15 # Max size for base64 encoded data (~11MB binary)

# --- File Processing Functions ---

def _run_ocr_on_pdf(input_pdf_path: str, output_pdf_path: str) -> bool:
    """Runs OCR on a PDF file using ocrmypdf."""
    if not ocrmypdf:
        logger.warning("ocrmypdf library is not available. Skipping OCR for PDF.")
        return False
    try:
        logger.info(f"Running OCR on PDF file: {input_pdf_path}")
        # Use English and Polish languages, force OCR
        result = ocrmypdf.ocr(input_pdf_path, output_pdf_path, language='eng+pol', force_ocr=True, progress_bar=False)
        if result == 0: # ocrmypdf returns 0 on success
             logger.info(f"OCR completed successfully for: {input_pdf_path}")
             return True
        else:
             logger.error(f"ocrmypdf finished with error code {result} for file {input_pdf_path}")
             return False
    except ocrmypdf.exceptions.TesseractNotFoundError:
         logger.error("Tesseract OCR not found by ocrmypdf.")
         # Change to ValueError to return 400 instead of 500 when OCR is unavailable
         raise ValueError("OCR engine (Tesseract) not found for PDF processing.")
    except Exception as ocr_e:
        logger.error(f"Error during OCR on PDF {input_pdf_path}: {ocr_e}", exc_info=True)
        return False # Return False to attempt extraction without OCR

def safe_extract_text_from_pdf(pdf_data: bytes) -> str:
    """Safely extracts text from PDF data using PyMuPDF, with OCR fallback."""
    if not fitz:
        # fitz is a core dependency, so RuntimeError is appropriate here
        raise RuntimeError("Required library PyMuPDF (fitz) is not installed.")

    text = ""
    temp_input_path = None
    temp_output_path = None

    try:
        # Check file size
        file_size_mb = len(pdf_data) / (1024 * 1024)
        if file_size_mb > MAX_PDF_SIZE_MB:
            raise ValueError(f"PDF file is too large. Maximum size is {MAX_PDF_SIZE_MB} MB.")

        # 1. Try text extraction using PyMuPDF
        try:
            with fitz.open(stream=pdf_data, filetype="pdf") as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text("text") # Extract plain text
                    if page_text:
                        text += page_text + "\n\n"
            logger.info(f"PyMuPDF: Extracted {len(text)} characters of text.")
        except Exception as fitz_e:
             logger.warning(f"Error during text extraction by PyMuPDF: {fitz_e}. Attempting OCR...")
             text = "" # Reset text if PyMuPDF failed

        # 2. If text is empty or insufficient, try OCR
        if not text.strip():
            if ocrmypdf:
                logger.warning("Text extracted by PyMuPDF is empty/insufficient. Attempting OCR with ocrmypdf...")
                try:
                    # Write data to temporary input file
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_in:
                        temp_in.write(pdf_data)
                        temp_input_path = temp_in.name

                    # Create path for temporary output file
                    temp_output_fd, temp_output_path = tempfile.mkstemp(suffix=".pdf")
                    os.close(temp_output_fd) # Close file descriptor

                    # Run OCR
                    ocr_success = _run_ocr_on_pdf(temp_input_path, temp_output_path)

                    if ocr_success and os.path.exists(temp_output_path):
                        # Read text from the OCR-processed file using PyMuPDF
                        text = "" # Reset text
                        with fitz.open(temp_output_path) as doc_ocr:
                            for page_num in range(len(doc_ocr)):
                                page = doc_ocr.load_page(page_num)
                                page_text = page.get_text("text")
                                if page_text:
                                    text += page_text + "\n\n"
                        logger.info(f"OCR: Extracted {len(text)} characters after OCR.")
                    else:
                         logger.error(f"OCR failed or output file does not exist: {temp_output_path}")
                         # If OCR fails, still return empty text but log the error
                         text = ""

                except Exception as ocr_pipeline_e:
                     logger.error(f"Error in OCR pipeline for PDF: {ocr_pipeline_e}", exc_info=True)
                     # If OCR fails, still return empty text but log the error
                     text = ""
                finally:
                     # Clean up temporary files
                     if temp_input_path and os.path.exists(temp_input_path):
                         try: os.unlink(temp_input_path)
                         except OSError: logger.warning(f"Could not delete temporary file: {temp_input_path}")
                     if temp_output_path and os.path.exists(temp_output_path):
                         try: os.unlink(temp_output_path)
                         except OSError: logger.warning(f"Could not delete temporary file: {temp_output_path}")
            else: # if ocrmypdf is not available
                 # If ocrmypdf is not available and text is empty, raise an error
                 logger.warning("Text extracted by PyMuPDF is empty, and ocrmypdf is not available for OCR fallback.")
                 raise ValueError("Could not extract text from PDF. OCR library (ocrmypdf) is not available.")

        # Final check if we have any text (after attempting OCR or if OCR wasn't needed/available)
        if not text.strip():
             logger.warning("Failed to extract meaningful text from PDF using PyMuPDF and OCR (if attempted).")
             # Return empty string if nothing found. Error is raised above if OCR was needed but unavailable.

        return text.strip()

    except (ValueError, RuntimeError) as e: # Catch specific errors first
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        # Re-raise as ValueError for the router to handle as 400 or 500 depending on the original type
        raise ValueError(f"Error processing PDF file: {e}") from e
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error processing PDF: {e}", exc_info=True)
        raise RuntimeError(f"Unexpected server error processing PDF: {e}") from e


def safe_extract_text_from_image(image_data: bytes) -> str:
    """Safely extracts text from image data using OCR. Raises ValueError on OCR/dependency errors."""
    if not Image or not pytesseract:
        # Change to ValueError
        raise ValueError("Image processing libraries (Pillow, pytesseract) are not installed.")

    text = ""
    suffix = '.png' # Default
    temp_path = None

    try:
        # Check image format to use correct extension for temporary file
        try:
            img_check = Image.open(io.BytesIO(image_data))
            if img_check.format:
                suffix = f'.{img_check.format.lower()}'
        except Exception:
            logger.warning("Could not determine image format, using default .png")

        # Write data to temporary file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name

        # Perform OCR
        image = Image.open(temp_path)
        # Ensure Tesseract path is set (can be done globally)
        # if os.getenv('TESSERACT_CMD'): pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD')
        text = pytesseract.image_to_string(image, lang='eng+pol') # Added Polish
        logger.info(f"Successfully performed OCR for image (size: {len(image_data)} B).")

    except pytesseract.TesseractNotFoundError:
         logger.error("Tesseract OCR is not installed or not found in PATH.")
         # Change to ValueError
         raise ValueError("OCR engine (Tesseract) is not available for image processing.")
    except Exception as e:
        logger.error(f"Error during image OCR processing: {e}", exc_info=True)
        # Raise as ValueError for consistency
        raise ValueError(f"Error during image OCR processing: {e}") from e
    finally:
        # Delete temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError as unlink_e:
                logger.warning(f"Could not delete temporary OCR file: {temp_path}. Error: {unlink_e}")
    return text

def safe_extract_text_from_markdown(md_data: bytes) -> str:
    """Converts Markdown to plain text. Raises ValueError on errors."""
    if not markdown or not BeautifulSoup:
         # Change to ValueError
         raise ValueError("Markdown processing libraries (Markdown, beautifulsoup4) are not installed.")
    try:
        md_text = md_data.decode('utf-8') # Assume UTF-8 for Markdown
        html = markdown.markdown(md_text)
        # Use html.parser as the parser, it's built-in
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        return text
    except Exception as e:
        logger.error(f"Error processing Markdown file: {e}", exc_info=True)
        raise ValueError(f"Error processing Markdown file: {e}") from e

def safe_extract_text_from_txt(txt_data: bytes) -> str:
    """Safely reads text from TXT data. Raises ValueError on errors."""
    encodings_to_try = ['utf-8', 'latin-1', 'cp1250', 'cp1252'] # List of encodings to try
    for encoding in encodings_to_try:
        try:
            return txt_data.decode(encoding)
        except UnicodeDecodeError:
            continue # Try next encoding
        except Exception as e:
             logger.error(f"Unexpected error decoding TXT as {encoding}: {e}", exc_info=True)
             raise ValueError(f"Error reading text file: {e}") from e # Raise error if not UnicodeDecodeError

    # If no encoding worked
    logger.error("Could not decode text file using standard encodings.")
    raise ValueError(f"Could not decode text file (tried: {', '.join(encodings_to_try)}).")


def process_uploaded_file_data(filename: str, file_data_base64: str) -> str:
    """
    Processes an uploaded file (base64 encoded) based on its type.
    Returns the extracted text or raises ValueError/RuntimeError on failure.
    """
    try:
        # Add size validation before decoding base64
        # Estimated base64 overhead is ~33%, so limit corresponds to ~11MB binary data
        max_base64_bytes = MAX_BASE64_SIZE_MB * 1024 * 1024
        if len(file_data_base64.encode('utf-8')) > max_base64_bytes: # Check bytes length
             raise ValueError(f"Encoded file data is too large (>{MAX_BASE64_SIZE_MB}MB).")

        file_data = base64.b64decode(file_data_base64)
        filename_lower = filename.lower()
        logger.info(f"Processing file: {filename} (decoded size: {len(file_data)} B)")

        # Add size validation for decoded image data
        max_image_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
        if filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')):
             if len(file_data) > max_image_bytes:
                  raise ValueError(f"Image file is too large (>{MAX_IMAGE_SIZE_MB}MB).")

        content = ""
        if filename_lower.endswith('.pdf'):
            content = safe_extract_text_from_pdf(file_data)
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')): # Expanded image list
            content = safe_extract_text_from_image(file_data)
        elif filename_lower.endswith('.md'):
            content = safe_extract_text_from_markdown(file_data)
        elif filename_lower.endswith('.txt'):
            content = safe_extract_text_from_txt(file_data)
        # Can add support for other types, e.g., .html, .docx, .pptx (requires additional libraries)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            raise ValueError(f"Unsupported file type: {os.path.splitext(filename)[1]}")

        # Truncate the extracted content if it exceeds the limit
        if len(content) > MAX_DOCUMENT_CHARS:
             logger.info(f"Truncated content of file {filename} to {MAX_DOCUMENT_CHARS} characters.")
             return content[:MAX_DOCUMENT_CHARS] + "... (truncated)"
        else:
             return content

    except (ValueError, RuntimeError) as e: # Catch specific errors first
        logger.error(f"Error processing file {filename}: {e}")
        # Re-raise specific ValueErrors or RuntimeErrors to be handled by the router
        raise e
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error in process_uploaded_file_data for {filename}: {e}", exc_info=True)
        # Raise a generic RuntimeError for unexpected issues
        raise RuntimeError("An unexpected server error occurred while processing the file.") from e
