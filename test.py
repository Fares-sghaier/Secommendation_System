from PIL import Image
import pytesseract
import requests
from io import BytesIO

def extract_text_from_image_url(url):
    """Extract text from an image URL using OCR."""
    try:
        response = r"C:\Users\Asus\OneDrive\Bureau\Master-Services-Agreement-Contract-Template-Example-01.jpg"

        extracted_text = pytesseract.image_to_string(response)
        return extracted_text.strip()
    except Exception as e:
        print(f"Image processing error: {str(e)}")
        return ""
    
def main():
    image_url = r"C:\Users\Asus\OneDrive\Bureau\Master-Services-Agreement-Contract-Template-Example-01.jpg"
    extracted_text = extract_text_from_image_url(image_url)
    if extracted_text:
        print("Extracted Text:")
        print(extracted_text)
    else:
        print("No text found in the image.")

if __name__ == "__main__":
    main()