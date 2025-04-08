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

RUN pip install langdetect
RUN pip install PyPDF2
#new
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



# Base image with Python
FROM python:3.10-slim

# Prevents interactive dialogs
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Tesseract OCR with Arabic and French support
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Optional: Define default command (update if you have a script)
CMD ["python", "app.py"]