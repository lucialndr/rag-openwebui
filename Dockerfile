FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Systemabhängigkeiten installieren (für PDF, Office, OCR)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    unoconv \
    libreoffice \
    tesseract-ocr \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Installiere nur PyTorch-Komponenten über den CPU-Index
RUN pip install --no-cache-dir --default-timeout=600 \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Installiere EasyOCR, MarkItDown (alle Formate), Flask
RUN pip install --no-cache-dir --default-timeout=600 \
    easyocr markitdown[all] flask

# App-Code kopieren
COPY app.py .

# Startbefehl
CMD ["python", "app.py"]

