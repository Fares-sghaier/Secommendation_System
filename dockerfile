FROM python:3.12-slim

# Install Tesseract and language packs
RUN apt-get update && \
    apt-get install -y tesseract-ocr \
    tesseract-ocr-eng tesseract-ocr-fra tesseract-ocr-ara && \
    apt-get clean

# Set the working directory
WORKDIR /app

# Copy app files
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Run your app
CMD ["python", "-X", "utf8", "app.py"]
