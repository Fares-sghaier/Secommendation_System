FROM python:3.12.2

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=fr_FR.UTF-8 \
    LANGUAGE=fr_FR.UTF-8

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
    pkg-config \
    wget \
    && locale-gen fr_FR.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create non-root user and switch to it
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Create necessary directories (ensure writable by appuser)
RUN mkdir -p /app/static/pdfs

# Copy application files
COPY --chown=appuser:appuser . .

# Expose port
EXPOSE 8000


# Command to run the application
CMD ["python", "app.py"]