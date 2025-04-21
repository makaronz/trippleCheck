import os
import base64
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.utils.file_processor import (
    safe_extract_text_from_pdf,
    safe_extract_text_from_image,
    safe_extract_text_from_txt,
    safe_extract_text_from_markdown,
    safe_extract_text_from_excel,
    safe_extract_text_from_powerpoint,
    safe_extract_text_from_rtf,
    safe_extract_text_from_archive,
    safe_extract_text_from_opendocument,
    safe_extract_text_from_xml,
    safe_extract_text_from_html,
    safe_extract_text_from_epub,
    format_extracted_text,
    process_uploaded_file_data,
    validate_file_type_and_scan
)

# Ścieżka do katalogu z plikami testowymi
TEST_FILES_DIR = Path(__file__).parent / "test_files"

def get_test_file_content(filepath: str) -> bytes:
    """Helper function to read test file content"""
    with open(filepath, 'rb') as f:
        return f.read()

def get_base64_content(filepath: str) -> str:
    """Helper function to get base64 encoded content"""
    return base64.b64encode(get_test_file_content(filepath)).decode()

# Testy dla walidacji typów plików
class TestFileValidation:
    def test_valid_file_type(self):
        """Test for valid file type validation"""
        test_pdf = TEST_FILES_DIR / "pdf" / "test.pdf"
        content = get_base64_content(str(test_pdf))
        is_valid, mime_type, _ = validate_file_type_and_scan("test.pdf", content)
        assert is_valid
        assert mime_type == "application/pdf"

    def test_invalid_file_type(self):
        """Test for invalid file type validation"""
        with pytest.raises(ValueError):
            validate_file_type_and_scan("test.exe", "invalid_content")

# Testy dla formatowania tekstu
class TestTextFormatting:
    def test_default_formatting(self):
        text = "  Line 1  \n\n  Line 2  \n  Line 3  "
        formatted = format_extracted_text(text, 'default')
        assert formatted == "Line 1\nLine 2\nLine 3"

    def test_structured_formatting(self):
        text = "HEADER\nContent line 1\nContent line 2\nSECTION\nMore content"
        formatted = format_extracted_text(text, 'structured')
        assert "=== HEADER ===" in formatted
        assert "=== SECTION ===" in formatted

    def test_compact_formatting(self):
        text = "Line 1\n\n\nLine 2   Line 3\n\nLine 4"
        formatted = format_extracted_text(text, 'compact')
        assert formatted == "Line 1\n\nLine 2 Line 3\n\nLine 4"

# Testy dla ekstrakcji tekstu z PDF
class TestPDFProcessing:
    @pytest.mark.asyncio
    async def test_pdf_text_extraction(self):
        """Test extracting text from PDF"""
        test_pdf = TEST_FILES_DIR / "pdf" / "test.pdf"
        with patch('fitz.open') as mock_open:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = "Test PDF content"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_open.return_value.__enter__.return_value = mock_doc
            
            content = get_test_file_content(str(test_pdf))
            result = safe_extract_text_from_pdf(content)
            assert "Test PDF content" in result

    @pytest.mark.asyncio
    async def test_pdf_ocr_fallback(self):
        """Test PDF OCR fallback when text extraction fails"""
        test_pdf = TEST_FILES_DIR / "pdf" / "scanned.pdf"
        with patch('fitz.open') as mock_open:
            mock_open.side_effect = Exception("Text extraction failed")
            with patch('ocrmypdf.ocr') as mock_ocr:
                mock_ocr.return_value = 0
                
                content = get_test_file_content(str(test_pdf))
                with pytest.raises(ValueError):
                    safe_extract_text_from_pdf(content)

# Testy dla ekstrakcji tekstu z obrazów
class TestImageProcessing:
    def test_image_ocr(self):
        """Test OCR on image"""
        test_image = TEST_FILES_DIR / "images" / "test.png"
        with patch('PIL.Image.open') as mock_open:
            mock_image = MagicMock()
            mock_open.return_value = mock_image
            with patch('pytesseract.image_to_string') as mock_ocr:
                mock_ocr.return_value = "Test image text"
                
                content = get_test_file_content(str(test_image))
                result = safe_extract_text_from_image(content)
                assert result == "Test image text"

# Testy dla plików tekstowych
class TestTextProcessing:
    def test_txt_file_processing(self):
        """Test processing text files"""
        test_txt = TEST_FILES_DIR / "text" / "test.txt"
        content = "Test text content".encode('utf-8')
        result = safe_extract_text_from_txt(content)
        assert result == "Test text content"

    def test_markdown_processing(self):
        """Test processing markdown files"""
        test_md = TEST_FILES_DIR / "text" / "test.md"
        content = "# Header\nTest content".encode('utf-8')
        with patch('markdown.markdown') as mock_markdown:
            mock_markdown.return_value = "<h1>Header</h1><p>Test content</p>"
            result = safe_extract_text_from_markdown(content)
            assert "Header" in result
            assert "Test content" in result

# Testy dla plików Office
class TestOfficeProcessing:
    def test_excel_xlsx_processing(self):
        """Test processing Excel XLSX files"""
        test_xlsx = TEST_FILES_DIR / "office" / "test.xlsx"
        with patch('openpyxl.load_workbook') as mock_load:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.sheetnames = ['Sheet1']
            mock_wb.__getitem__.return_value = mock_ws
            mock_ws.iter_rows.return_value = [[MagicMock(value='Test')]]
            mock_load.return_value = mock_wb
            
            content = get_test_file_content(str(test_xlsx))
            result = safe_extract_text_from_excel(
                content, 
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            assert 'Test' in result

    def test_powerpoint_processing(self):
        """Test processing PowerPoint files"""
        test_pptx = TEST_FILES_DIR / "office" / "test.pptx"
        with patch('pptx.Presentation') as mock_pres:
            mock_slide = MagicMock()
            mock_shape = MagicMock()
            mock_shape.text = "Test slide content"
            mock_slide.shapes = [mock_shape]
            mock_pres.return_value.slides = [mock_slide]
            
            content = get_test_file_content(str(test_pptx))
            result = safe_extract_text_from_powerpoint(content)
            assert "Test slide content" in result

# Testy dla archiwów
class TestArchiveProcessing:
    def test_zip_processing(self):
        """Test processing ZIP archives"""
        test_zip = TEST_FILES_DIR / "archives" / "test.zip"
        with patch('zipfile.ZipFile') as mock_zip:
            mock_zip.return_value.__enter__.return_value.namelist.return_value = ['test.txt']
            
            content = get_test_file_content(str(test_zip))
            result = safe_extract_text_from_archive(content, 'application/zip')
            assert 'test.txt' in result

# Testy dla XML i HTML
class TestMarkupProcessing:
    def test_xml_processing(self):
        """Test processing XML files"""
        test_xml = TEST_FILES_DIR / "xml" / "test.xml"
        xml_content = b'<?xml version="1.0"?><root><item>Test</item></root>'
        result = safe_extract_text_from_xml(xml_content)
        assert 'Test' in result

    def test_html_processing(self):
        """Test processing HTML files"""
        test_html = TEST_FILES_DIR / "html" / "test.html"
        with patch('readability.Document') as mock_doc:
            mock_doc.return_value.summary.return_value = "<p>Test content</p>"
            
            content = get_test_file_content(str(test_html))
            result = safe_extract_text_from_html(content)
            assert "Test content" in result

# Testy dla EPUB
class TestEPUBProcessing:
    def test_epub_processing(self):
        """Test processing EPUB files"""
        test_epub = TEST_FILES_DIR / "epub" / "test.epub"
        with patch('ebooklib.epub.read_epub') as mock_read:
            mock_book = MagicMock()
            mock_book.get_metadata.return_value = [('Test Title',)]
            mock_item = MagicMock()
            mock_item.get_type.return_value = 'ITEM_DOCUMENT'
            mock_item.get_content.return_value = "<p>Test content</p>"
            mock_book.get_items.return_value = [mock_item]
            mock_read.return_value = mock_book
            
            content = get_test_file_content(str(test_epub))
            result = safe_extract_text_from_epub(content)
            assert "Test content" in result

# Testy integracyjne
class TestIntegration:
    def test_complete_file_processing(self):
        """Test complete file processing pipeline"""
        test_file = TEST_FILES_DIR / "text" / "test.txt"
        content = get_base64_content(str(test_file))
        result = process_uploaded_file_data(content, "test.txt")
        assert isinstance(result, dict)
        assert "text" in result
        assert "mime_type" in result
        assert "filename" in result

    @pytest.mark.asyncio
    async def test_multiple_file_formats(self):
        """Test processing multiple file formats in sequence"""
        formats = [
            ("test.txt", "text/plain"),
            ("test.pdf", "application/pdf"),
            ("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("test.html", "text/html"),
            ("test.epub", "application/epub+zip")
        ]
        
        for filename, mime_type in formats:
            with patch('magic.Magic') as mock_magic:
                mock_magic.return_value.from_buffer.return_value = mime_type
                content = base64.b64encode(b"Test content").decode()
                result = process_uploaded_file_data(content, filename)
                assert result["mime_type"] == mime_type 