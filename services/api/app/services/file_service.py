from fastapi import UploadFile
import pytesseract
from PIL import Image
from io import BytesIO
import time
from api.app.services.ocr_extraction import extract_text_from_image_object_api, extract_text_from_pdf_bytes_api

# Try to import PyMuPDF with fallback
try:
    import fitz  # PyMuPDF - make sure this is the right package
    HAS_PYMUPDF = True
except ImportError as e:
    HAS_PYMUPDF = False
    print(f"Warning: PyMuPDF not available: {e}. PDF processing will be disabled.")

# -------- Function to extract text from PIL Image object --------
def extract_text_from_image_object(image_obj: Image.Image):
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    return pytesseract.image_to_string(image_obj)

# -------- Function to extract text from PDF bytes --------
def extract_text_from_pdf_bytes(pdf_bytes: bytes):
    if not HAS_PYMUPDF:
        raise ImportError("PyMuPDF is not available. Cannot process PDF files.")
    
    text = ""
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    zoom = 3
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text += pytesseract.image_to_string(img) + "\n"

    return text

def convert_file_to_string(file: UploadFile) -> str:
    # Read file contents into memory first
    file_contents = file.file.read()
    # Reset file pointer
    file.file.seek(0)
    
    if file.content_type in ["image/jpeg", "image/png"]:
        # Create PIL Image from bytes using BytesIO
        image = Image.open(BytesIO(file_contents))
        return extract_text_from_image_object_api(image)
    elif file.content_type == "application/pdf":
        if not HAS_PYMUPDF:
            raise ValueError("PDF processing is not available. PyMuPDF is not installed.")
        return extract_text_from_pdf_bytes_api(file_contents)
    else:
        raise ValueError(f"Unsupported file type: {file.content_type}")


