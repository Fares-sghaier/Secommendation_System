FROM python:3.12.2

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    libpoppler-cpp-dev \
    libxml2-dev \
    libxslt1-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    libtesseract-dev \
    libleptonica-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    poppler-utils \
    && locale-gen fr_FR.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    pytesseract \
    langdetect \
    PyPDF2 \
    arabic-reshaper \
    python-bidi \
    pycryptodome \
    Flask \
    pillow

# Verify Tesseract installation
RUN tesseract --version

# Create necessary directories
RUN mkdir -p /app/static/pdfs

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "app.py"]