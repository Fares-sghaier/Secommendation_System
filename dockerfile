FROM python:3.12.2

# Set working directory
WORKDIR /app

#RUN mkdir -p /app/fonts

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    libpoppler-cpp-dev \
    libxml2-dev \
    libxslt1-dev \
    && locale-gen fr_FR.UTF-8 \
    && apt-get clean \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pytesseract

RUN pip install langdetect
RUN pip install PyPDF2

RUN pip install arabic-reshaper
RUN pip install python-bidi
RUN pip install pycryptodome

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

#new
RUN mkdir -p /app/static/pdfs

# Copy application files
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "app.py"]


