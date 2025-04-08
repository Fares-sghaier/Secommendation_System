FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies and tesseract
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    libtesseract-dev \
    libleptonica-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Install dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr \
    tesseract-ocr-eng tesseract-ocr-fra tesseract-ocr-ara && \
    apt-get clean

RUN apt-get install ffmpeg -y
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]

