import requests
from PIL import Image
from io import BytesIO
import time
import fitz  # PyMuPDF
import io

OCR_API_KEY = "K81831870088957"
OCR_API_URL = "https://api.ocr.space/parse/image"

# -------- Function to extract text from PIL Image object using OCR.space API --------
def extract_text_from_image_object_api(image_obj: Image.Image):
    buffered = BytesIO()
    image_obj.save(buffered, format="PNG")
    buffered.seek(0)

    files = {'file': ('image.png', buffered)}
    data = {'language': 'eng', 'isOverlayRequired': False}

    response = requests.post(OCR_API_URL, files=files, data=data, headers={'apikey': OCR_API_KEY})
    result = response.json()

    if result.get("IsErroredOnProcessing"):
        raise RuntimeError(result.get("ErrorMessage", ["Unknown error"])[0])
    
    return "\n".join([r["ParsedText"] for r in result.get("ParsedResults", [])])

# -------- Function to extract text from PDF bytes using OCR.space API --------
def extract_text_from_pdf_bytes_api(pdf_bytes: bytes):
    """Convert PDF to high-res images, then OCR each page"""
    text_results = []
    
    # Open PDF from bytes
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    for page_num in range(len(pdf_document)):
        print(f"Processing page {page_num + 1}...")
        
        # Convert page to high-resolution image
        page = pdf_document[page_num]
        zoom = 3  # Higher zoom = better quality
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # OCR the image
        page_text = extract_text_from_image_object_api(img)
        text_results.append(page_text)
        
        print(f"Page {page_num + 1} text length: {len(page_text)} characters")
    
    pdf_document.close()
    return "\n\n--- PAGE BREAK ---\n\n".join(text_results)

# -------- Example Usage --------
if __name__ == "__main__":
    # Example with an image object
    start_img = time.time()
    with Image.open("legitimate_image.png") as img_obj:
        image_text = extract_text_from_image_object_api(img_obj)
    end_img = time.time()
    print("Text from image object:\n", image_text)
    print(f"Extraction time (image): {end_img - start_img:.2f} seconds\n")

    # Example with PDF bytes
    start_pdf = time.time()
    with open("Apple Cover Letter.pdf", "rb") as f:
        pdf_bytes = f.read()
        pdf_text = extract_text_from_pdf_bytes_api(pdf_bytes)
    end_pdf = time.time()
    print("Text from PDF bytes:\n", pdf_text)
    print(f"Extraction time (PDF): {end_pdf - start_pdf:.2f} seconds\n")
