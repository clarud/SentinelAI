import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from io import BytesIO
import time

# -------- Function to extract text from PIL Image object --------
def extract_text_from_image_object(image_obj: Image.Image):
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

# -------- Example Usage --------
if __name__ == "__main__":
    # Example with an image object
    start_img = time.time()
    with Image.open("legitimate_image.png") as img_obj:
        image_text = extract_text_from_image_object(img_obj)
    end_img = time.time()
    print("Text from image object:\n", image_text)
    print(f"Extraction time (image): {end_img - start_img:.2f} seconds\n")

    # Example with PDF bytes
    start_pdf = time.time()
    with open("legitimate_pdf.pdf", "rb") as f:
        pdf_bytes = f.read()
        pdf_text = extract_text_from_pdf_bytes(pdf_bytes)
    end_pdf = time.time()
    print("Text from PDF bytes:\n", pdf_text)
    print(f"Extraction time (PDF): {end_pdf - start_pdf:.2f} seconds\n")