from fastapi import UploadFile
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from io import BytesIO
import time

# -------- Function to extract text from PIL Image object --------
def extract_text_from_image_object(image_obj: Image.Image):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    return pytesseract.image_to_string(image_obj)

# -------- Function to extract text from PDF bytes --------
def extract_text_from_pdf_bytes(pdf_bytes: bytes):
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
        # Create PIL Image from bytes instead of file stream
        image = Image.open(BytesIO(file_contents))
        return extract_text_from_image_object(image)
    elif file.content_type == "application/pdf":
        return extract_text_from_pdf_bytes(file_contents)
    else:
        raise ValueError(f"Unsupported file type: {file.content_type}")


