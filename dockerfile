FROM python:3.12.2

# Set environment variables for Tesseract and Python path
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages
# Ensure Tesseract is in the PATH
ENV PATH="/usr/bin:$PATH"

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
    pkg-config \
    && locale-gen fr_FR.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation and data
RUN tesseract --version && \
    tesseract --list-langs && \
    ls -l /usr/share/tesseract-ocr/4.00/tessdata

# Install Python packages
RUN pip install --no-cache-dir \
    pytesseract==0.3.10 \
    langdetect \
    PyPDF2 \
    arabic-reshaper \
    python-bidi \
    pycryptodome \
    Flask \
    pillow

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