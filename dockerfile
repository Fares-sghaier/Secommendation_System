# Use official Python image with full system dependencies
FROM python:3.12.2-slim-bullseye

# Set environment variables for Python and locale
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=fr_FR.UTF-8 \
    LANGUAGE=fr_FR.UTF-8 \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/tessdata

# Set working directory
WORKDIR /app

# Install system dependencies with proper cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    libpoppler-cpp-dev \
    libxml2-dev \
    libxslt1-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-osd \  # For script detection
    libtesseract-dev \
    libleptonica-dev \
    # Image processing libraries
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libjpeg62-turbo \
    libpng16-16 \
    libwebp6 \
    libopenjp2-7 \
    # System utilities
    poppler-utils \
    wget \
    && locale-gen fr_FR.UTF-8 \
    && mkdir -p ${TESSDATA_PREFIX} \
    && ln -s /usr/share/tesseract-ocr/*/tessdata/* ${TESSDATA_PREFIX} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation and languages
RUN tesseract --version && tesseract --list-langs

# Install Python dependencies in optimized order
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create non-root user with necessary permissions
RUN useradd -m appuser \
    && mkdir -p /app/static/pdfs \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Copy application files with proper ownership
COPY --chown=appuser:appuser . .

# Set final working environment
WORKDIR /app

# Expose port
EXPOSE 8000

# Entrypoint command
CMD ["python", "app.py"]