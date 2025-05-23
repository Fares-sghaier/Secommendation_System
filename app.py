from flask import Flask, request, jsonify, url_for
import os
import re
from flask_cors import CORS
from openai import AzureOpenAI
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import PyPDF2
import sys
import requests
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pytesseract
import PIL
from io import BytesIO

# Configure system encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import docx2txt


# Font URL
FONT_URL = "https://raw.githubusercontent.com/frappe/fonts/master/usr_share_fonts/noto/NotoNaskhArabic-Regular.ttf"

app = Flask(__name__)
CORS(app)
import os
import subprocess


def get_mime_type_from_headers(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.headers.get('Content-Type', '').lower()
    except Exception as e:
        return None
# Language-specific configurations
LANGUAGE_CONFIGS = {
    'en': {
        'sections': {
            'Missing Articles/Clauses': [],
            'Problem Description': [],
            'Recommendation': []
        },
        'pdf_title': "Contract Analysis",
        'system_prompt': """You are a specialized legal assistant. Analyze the contract strictly according to the following structure:

Missing Articles/Clauses:  
Problem Description:  
Recommendation:  

Instructions:
- Provide recommendations as a bulleted list.
- Example:
• Recommendation 1  
• Recommendation 2


Return EXACTLY the following message if the text did not need any recommendations:
Missing Articles/Clauses: No missing articles or clauses found  
Problem Description: No problem description found  
Recommendation: No recommendations found


IMPORTANT:
If the input text is not a contract, DO NOT invent or fabricate any content, and return the message "the document should be a contract".

DO NOT HALLUCINATE OR MAKE UP ANYTHING. JUST RETURN THE MESSAGE AS IT IS.
"""
    },
    'fr': {
        'sections': {
            'Articles/Clauses Manquantes': [],
            'Description du problème': [],
            'Recommandation': []
        },
        'pdf_title': "Analyse du Contrat",
        'system_prompt': """Vous êtes un assistant juridique spécialisé. Analysez le contrat selon la structure suivante :

Articles/Clauses Manquantes :  
Description du problème :  
Recommandation :  

Instructions :
- Fournissez les recommandations sous forme de liste à puces.
- Exemple :
• Recommandation 1  
• Recommandation 2



Retournez UNIQUEMENT le message suivant si le texte n'a pas besoin de recommandations :
Articles/Clauses Manquantes :  \n
• il n'y a pas d'articles ou de clauses manquantes  \n
Description du problème :  \n
• il n'y a pas de description de problème  \n
Recommandation :  \n
• il n'y a pas de recommandations trouvées \n

IMPORTANT :
Si le texte n'est pas un contrat, NE GÉNÉREZ RIEN. retournez UNIQUEMENT le message suivant : "le document doit être un contrat".
NE GÉNÉREZ RIEN DE PLUS. NE FAITES PAS D’HALLUCINATIONS. RETOURNEZ LE MESSAGE TEL QUEL.
"""
    },
    'ar': {
        'sections': {
            'المواد و البنود المفقودة': [],
            'وصف المشكلة': [],
            'التوصية': []
        },
        'pdf_title': "تحليل العقد",
        'system_prompt': """أنت مساعد قانوني متخصص. قم بتحليل العقد وفقاً للبنية التالية:

المواد و البنود المفقودة:  
وصف المشكلة:  
التوصية:  

التعليمات:
- قدم التوصيات في شكل نقاط.
- مثال:
• التوصية 1  
• التوصية 2


  ارجع فقط بالرسالة التالية:

المواد و البنود المفقودة:  \n
• لا توجد مواد أو بنود مفقودة \n 
وصف المشكلة:  \n
• لا توجد مشكلة  \n
التوصية:  \n
• لا توجد توصيات\n

هام:
إذا كان النص ليس عقدًا ، لا تخترع أي محتوى. إرجع فقط بالرسال "يجب أن يكون الملف عقدا" 
لا تختلق أو تضيف أي شيء. فقط أعد الرسالة كما هي.
"""
    }
}


# Create necessary directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, 'static', 'pdfs')
os.makedirs(PDF_DIR, exist_ok=True)

# Configure Flask app
app.config.update(
    JSON_AS_ASCII=False,
    JSONIFY_MIMETYPE='application/json; charset=utf-8',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

load_dotenv()


client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
)
deployment_name = "gpt-4"

def download_and_register_font():
    """Download and register the Arabic font"""
    try:
        response = requests.get(FONT_URL)
        if response.status_code == 200:
            font_data = BytesIO(response.content)
            pdfmetrics.registerFont(TTFont('NotoArabic', font_data))
            return True
    except Exception as e:
        print(f"Error downloading font: {str(e)}")
        return False

def process_arabic_text(text):
    """Process Arabic text for proper display in PDF"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def detect_language(text):
    try:
        lang = detect(text)
        if lang not in LANGUAGE_CONFIGS:
            lang = 'en'  # Default to English if language not supported
        return lang
    except LangDetectException:
        return 'en'

def get_styles(language='en'):
    styles = getSampleStyleSheet()
    
    # Font configuration
    base_font = 'NotoArabic' if language == 'ar' else 'Helvetica'
    
    # RTL alignment for Arabic
    alignment = 2 if language == 'ar' else 1  # 2 for right alignment, 1 for center
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.HexColor('#2c3e50'),
        backColor=colors.HexColor('#ecf0f1'),
        borderPadding=(10, 10, 10, 10),
        borderWidth=1,
        borderColor=colors.HexColor('#3498db'),
        alignment=alignment,
        fontName=base_font
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15,
        leftIndent=10 if language != 'ar' else 0,
        rightIndent=0 if language != 'ar' else 10,
        borderColor=colors.HexColor('#3498db'),
        borderWidth=0,
        borderPadding=(5, 0, 5, 0),
        alignment=2 if language == 'ar' else 0,
        fontName=base_font
    )
    
    content_style = ParagraphStyle(
        'CustomContent',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6,
        bulletIndent=20,
        leftIndent=20 if language != 'ar' else 0,
        rightIndent=0 if language != 'ar' else 20,
        alignment=2 if language == 'ar' else 0,
        fontName=base_font
    )
    
    return title_style, section_style, content_style
def create_pdf(content_list, language='en'):
    # Ensure font is registered before creating PDF
    if language == 'ar' and not download_and_register_font():
        print("Warning: Could not load Arabic font, falling back to default")

    filename = f"recommendation.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    title_style, section_style, content_style = get_styles(language)
    elements = []

    # Add main title
    title_text = LANGUAGE_CONFIGS[language]['pdf_title']
    if language == 'ar':
        title_text = process_arabic_text(title_text)
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 20))

    # Process content
    for item in content_list:
        text = item['text']
        if language == 'ar':
            text = process_arabic_text(text)

        if item['type'] == 'header':
            elements.append(Paragraph(text, section_style))
        elif item['type'] == 'bullet':
            bullet = '•' if language != 'ar' else '•'
            elements.append(Paragraph(f"{bullet} {text}", content_style))
            elements.append(Spacer(1, 5))
        elif item['type'] == 'plain':
            # Add plain text without bullet
            elements.append(Paragraph(text, content_style))
            elements.append(Spacer(1, 5))

    # Add logo at the bottom of the page
    logo_path = os.path.join(BASE_DIR, 'logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=1*inch, height=1*inch)
        img.hAlign = 'CENTER'
        elements.append(Spacer(1, 20))
        elements.append(img)

    # Add metadata (title and author)
    def add_metadata(canvas, doc):
        canvas.setTitle("E-Tafakna Recommendations")
        canvas.setAuthor("E-Tafakna")

    doc.build(elements, onFirstPage=add_metadata)

    return url_for('static', filename=f'pdfs/{filename}', _external=True)

def predict_suggestions(input_text, language):
    try:
        completion = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": LANGUAGE_CONFIGS[language]['system_prompt']
                },
                {"role": "user", "content": input_text}
            ],
            max_tokens=1000,
            temperature=0.7,
            top_p=0.8,
            presence_penalty=0
)  
        
        
        response_content = completion.choices[0].message.content
        return format_response(response_content, language)
    except Exception as e:
        return {"error": str(e)}
    

def extract_pdf_text_from_url(url):
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch PDF: Status code {response.status_code}")
            return ""

        raw_data = response.content
        extracted_text = ""

        with BytesIO(raw_data) as data:
            try:
                read_pdf = PyPDF2.PdfReader(data)

                # Decrypt if the PDF is encrypted
                if read_pdf.is_encrypted:
                    try:
                        read_pdf.decrypt("")  # Try decrypting with an empty password
                    except Exception as decrypt_error:
                        print(f"Decryption error: {str(decrypt_error)}")
                        return ""

                extracted_text = " ".join(page.extract_text() for page in read_pdf.pages)
            except Exception as e:
                print(f"PDF processing error: {str(e)}")
                return ""

        return extracted_text
    except Exception as e:
        print(f"General error: {str(e)}")
        return ""



def format_response(text, language):

    if text == "the document should be a contract" or text == "يجب أن يكون الملف عقدا"or text == "le document doit être un contrat":
        return {
            'pdf_url': None,
            'text': text
        }
    if isinstance(text, bytes):
        text = text.decode('utf-8')

    sections = LANGUAGE_CONFIGS[language]['sections'].copy()
    formatted_content = []
    current_section = None
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        is_header = False
        for section in sections:
            # Check if line starts with section header followed by a colon
            if line.startswith(f"{section}:"):
                current_section = section
                formatted_content.append({"type": "header", "text": current_section})
                # Extract content after colon
                content = line.split(':', 1)[1].strip()
                if content:
                    formatted_content.append({"type": "plain", "text": content})
                is_header = True
                break
            elif section.lower() in line.lower() or (language == 'ar' and section in line):
                current_section = section
                formatted_content.append({"type": "header", "text": current_section})
                is_header = True
                break
        
        if not is_header and current_section:
            # Check if line starts with a bullet
            bullet_match = re.match(r'^[-•*]\s*(.*)', line)
            if bullet_match:
                cleaned_line = bullet_match.group(1).strip()
                formatted_content.append({"type": "bullet", "text": cleaned_line})
            else:
                formatted_content.append({"type": "plain", "text": line})

    # Create PDF with structured content
    pdf_url = create_pdf(formatted_content, language)
    
    return {
        'pdf_url': pdf_url.replace('http://', 'https://'),
        'text': text
    }

def extract_text_from_image_url(url):
    """Extract text from an image URL using OCR."""
    try:
        print(f"Processing image URL: {url}")
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch image: Status code {response.status_code}")
            return ""

        image = PIL.Image.open(BytesIO(response.content))
        print(f"Image opened successfully: {image.format}, size: {image.size}")
        
        # Check tesseract configuration
        print(f"Using tesseract at: {pytesseract.pytesseract.tesseract_cmd}")
        
        try:
            extracted_text = pytesseract.image_to_string(image, lang='ara+eng+fra')
            print(f"OCR successful, extracted {len(extracted_text)} characters")
            return extracted_text.strip()
        except Exception as ocr_e:
            print(f"OCR failed: {str(ocr_e)}")
            
            # Fallback: Try with just English
            try:
                print("Trying fallback OCR with English only...")
                extracted_text = pytesseract.image_to_string(image, lang='eng')
                return extracted_text.strip()
            except Exception as fallback_e:
                print(f"Fallback OCR failed: {str(fallback_e)}")
                return ""
            
    except Exception as e:
        print(f"Image processing error: {str(e)}")
        return ""
def extract_text_from_docx_url(url):
    response = requests.get(url)
    docx_file = BytesIO(response.content)
    text = docx2txt.process(docx_file)
    return text

@app.route('/get-pdf-suggestions', methods=['POST'])
def get_pdf_suggestions():
    try:
        # Get the user input from the request
        pdf_url = request.form.get('pdf_url')
        image_url = request.form.get('image_url')

        if not pdf_url and not image_url:
            sys.stdout.write("No URL provided in form data\n")
            sys.stdout.flush()
            return jsonify({"error": "No URL provided"}), 400
        
        extracted_text = ""
        
        if pdf_url:
            mime_type = get_mime_type_from_headers(pdf_url)
            if mime_type and 'application/pdf' in mime_type:
                extracted_text = extract_pdf_text_from_url(pdf_url)
            elif mime_type and 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in mime_type:
                extracted_text = extract_text_from_docx_url(pdf_url)
            elif mime_type and 'application/msword' in mime_type:
                extracted_text = extract_text_from_docx_url(pdf_url)
            else:
                sys.stdout.write("Invalid PDF URL or MIME type\n")
                sys.stdout.flush()
                return jsonify({"error": "Invalid PDF URL or MIME type"}), 400
        elif image_url:
            mime_type = get_mime_type_from_headers(image_url)
            if mime_type and 'image/' in mime_type:
                extracted_text = extract_text_from_image_url(image_url)
            else:
                sys.stdout.write("Invalid image URL or MIME type\n")
                sys.stdout.flush()
                return jsonify({"error": "Invalid image URL or MIME type"}), 400
            
        sys.stdout.write(f"Successfully extracted text of length: {len(extracted_text)}\n")
        sys.stdout.flush()
        language = detect_language(extracted_text)
        suggestions = predict_suggestions(extracted_text, language)
        print
        return jsonify({"suggestions": suggestions})
    except Exception as e:
        sys.stdout.write(f"Endpoint error: {str(e)}\n")
        sys.stdout.flush()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
