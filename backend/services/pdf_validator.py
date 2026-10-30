import io
from pypdf import PdfReader
from flask import current_app

class PDFValidationError(Exception):
    def __init__(self, message: str, code: str = "INVALID_PDF"):
        self.message = message
        self.code = code
        super().__init__(self.message)

def validate_pdf_file(file_bytes: bytes, filename: str) -> dict:
    """
    Server-side PDF validation pipeline:
    1. Check file size
    2. Check extension
    3. Check magic byte signature (%PDF-)
    4. Parse with pypdf (detect corruption / fake PDFs)
    5. Check page count > 0
    6. Check for blank PDF (rejects zero text & zero image/graphic content)
    """
    if not file_bytes:
        raise PDFValidationError("Uploaded file is empty.", "EMPTY_FILE")
        
    max_size = current_app.config.get('MAX_UPLOAD_SIZE', 25 * 1024 * 1024)
    if len(file_bytes) > max_size:
        raise PDFValidationError(
            f"File size exceeds maximum allowed limit of {max_size // (1024 * 1024)}MB.", 
            "FILE_TOO_LARGE"
        )

    # 1. Extension check
    if filename and not filename.lower().endswith('.pdf'):
        raise PDFValidationError("Only .pdf files are accepted.", "INVALID_EXTENSION")

    # 2. Magic Bytes Signature Check (%PDF- -> \x25\x50\x44\x46)
    if not file_bytes.startswith(b'%PDF-'):
        raise PDFValidationError("This file is not a valid PDF document (invalid magic header).", "INVALID_MAGIC_HEADER")

    # 3. Parse PDF with pypdf
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
    except Exception as e:
        raise PDFValidationError(f"This PDF could not be opened or is corrupted. Details: {str(e)}", "CORRUPTED_PDF")

    # 4. Check page count
    try:
        page_count = len(reader.pages)
    except Exception:
        raise PDFValidationError("Failed to read pages from PDF document.", "CORRUPTED_PAGES")

    if page_count <= 0:
        raise PDFValidationError("PDF document contains 0 pages.", "ZERO_PAGES")

    # 5. Blank PDF Test - Inspect text and image contents across all pages
    total_text_length = 0
    total_images = 0
    extracted_text_pages = []

    for idx, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            cleaned_text = text.strip()
            total_text_length += len(cleaned_text)
            extracted_text_pages.append(cleaned_text)
        except Exception:
            extracted_text_pages.append("")

        # Check for images or vector graphics in page resources
        try:
            images = page.images
            if images:
                total_images += len(images)
        except Exception:
            pass
            
        # Check /Resources /XObject if page.images doesn't pick up scanned pages
        if total_images == 0:
            try:
                res = page.get('/Resources')
                if res and isinstance(res, dict) and '/XObject' in res:
                    total_images += 1
            except Exception:
                pass

    # Reject if zero meaningful text AND zero images/visual elements
    if total_text_length < 5 and total_images == 0:
        raise PDFValidationError(
            "This PDF appears to be blank or contains no meaningful content.", 
            "BLANK_PDF"
        )

    full_extracted_text = " ".join(extracted_text_pages).strip()

    return {
        "valid": True,
        "page_count": page_count,
        "file_size": len(file_bytes),
        "total_text_length": total_text_length,
        "total_images": total_images,
        "extracted_text": full_extracted_text
    }
