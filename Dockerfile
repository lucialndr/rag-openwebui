FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=600

WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    unoconv \
    libreoffice \
    tesseract-ocr \
    libgl1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten installieren (CPU-only Torch + OCR + markitdown)
RUN pip install --no-cache-dir --default-timeout=600 \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    easyocr \
    markitdown[all] \
    flask

COPY app.py .

CMD ["python", "app.py"]
