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
from io import BytesIO
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


# Configure system encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Font URL
FONT_URL = "https://raw.githubusercontent.com/frappe/fonts/master/usr_share_fonts/noto/NotoNaskhArabic-Regular.ttf"

app = Flask(__name__)
CORS(app)

# Language-specific configurations
LANGUAGE_CONFIGS = {
    'en': {
        'sections': {
            'Missing Articles/Clauses': [],
            'Problem Description': [],
            'Recommendation': []
        },
        'pdf_title': "Contract Analysis",
        'system_prompt': """You are a specialized legal assistant. Analyze the contract according to the structure:
Missing Articles/Clauses: 
Problem Description:
Recommendation: 
-give an example of recommendation"""
    },
    'fr': {
        'sections': {
            'Articles/Clauses Manquantes': [],
            'Description du problème': [],
            'Recommandation': []
        },
        'pdf_title': "Analyse du Contrat",
        'system_prompt': """Vous êtes un assistant juridique spécialisé. Analysez le contrat selon la structure:
Articles/Clauses Manquantes: 
Description du problème:
Recommandation:
-donne un exemple de recommandation"""
    },
    'ar': {
        'sections': {
            'المواد و البنود المفقودة': [],
            'وصف المشكلة': [],
            'التوصية': []
        },
        'pdf_title': "تحليل العقد",
        'system_prompt': """  اكتب في شكل اسطر و ليس فقرات.أنت مساعد قانوني متخصص. قم بتحليل العقد وفقاً للهيكل التالي:
المواد و البنود المفقودة:
وصف المشكلة:
التوصية:
-قدم مثالا في سطر واحد على كل توصية"""
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

# Load Azure OpenAI configuration
load_dotenv()
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION')
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
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}.pdf"
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
        else:
            bullet = '•' if language != 'ar' else '•'
            elements.append(Paragraph(f"{bullet} {text}", content_style))
            elements.append(Spacer(1, 5))

    # Add logo at the bottom of the page
    logo_path = os.path.join(BASE_DIR, 'logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=1*inch, height=1*inch)
        img.hAlign = 'CENTER'
        elements.append(Spacer(1, 20))
        elements.append(img)

    doc.build(elements)
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
            temperature=0.5,
            top_p=0.8,
            presence_penalty=0,
            stream=False
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
            if section.lower() in line.lower() or (language == 'ar' and section in line):
                current_section = section
                formatted_content.append({"type": "header", "text": current_section})
                is_header = True
                break
        
        if not is_header and current_section:
            cleaned_line = re.sub(r'^[-•*]\s*', '', line)
            if cleaned_line:
                formatted_content.append({"type": "content", "text": cleaned_line})

    # Create PDF with structured content
    pdf_url = create_pdf(formatted_content, language)
    
    return {
        'pdf_url': pdf_url,
        'text': text
    }

@app.route('/get-pdf-suggestions', methods=['POST'])
def get_pdf_suggestions():
    pdf_url = request.form.get('url')
    if not pdf_url:
        return jsonify({"error": "URL not provided"}), 400

    extracted_text = extract_pdf_text_from_url(pdf_url)
    if not extracted_text:
        return jsonify({"error": "Failed to extract text from PDF"}), 400

    language = detect_language(extracted_text)
    suggestions = predict_suggestions(extracted_text, language)
    return jsonify({"suggestions": suggestions})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
